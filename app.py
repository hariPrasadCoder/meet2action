"""Meet2Action - Main Streamlit application."""
import streamlit as st
import datetime
from components.auth import login_form, logout_button, is_logged_in, get_user_session
from components.drive_connector import connect_google_drive, fetch_transcripts, get_transcript_content
from components.transcript_parser import parse_transcript, clean_transcript
from components.gemini_processor import extract_action_items
from components.kanban_board import display_kanban_board, display_tasks_summary
from utils.supabase_client import save_tasks, fetch_tasks
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# Page configuration
st.set_page_config(
    page_title="Meet2Action",
    page_icon="📋",
    layout="wide"
)

# Initialize session state
if 'google_creds' not in st.session_state:
    st.session_state.google_creds = None
if 'transcripts' not in st.session_state:
    st.session_state.transcripts = []
if 'selected_transcript' not in st.session_state:
    st.session_state.selected_transcript = None
if 'action_items' not in st.session_state:
    st.session_state.action_items = []
if 'transcript_content' not in st.session_state:
    st.session_state.transcript_content = None


def main():
    """Main application flow."""
    st.title("📋 Meet2Action")
    st.markdown("Transform Google Meet transcripts into actionable Kanban boards")
    
    # Sidebar for authentication
    with st.sidebar:
        st.header("🔐 Authentication")
        
        if not is_logged_in():
            login_form()
        else:
            user = get_user_session()
            if user:
                st.success(f"Logged in as: {user.email}")
                logout_button()
                st.markdown("---")
                
                # Show saved tasks option
                if st.button("📥 Load Saved Tasks"):
                    user_tasks = fetch_tasks(user.id)
                    if user_tasks:
                        # Convert to action items format
                        st.session_state.action_items = [
                            {
                                "assignee": task.get("assignee", "Unassigned"),
                                "task": task.get("task", ""),
                                "priority": task.get("priority", "Medium")
                            }
                            for task in user_tasks
                        ]
                        st.success(f"Loaded {len(user_tasks)} saved task(s)")
                        st.rerun()
                    else:
                        st.info("No saved tasks found.")
    
    # Main content area
    if not is_logged_in():
        st.info("👈 Please log in using the sidebar to continue.")
        return
    
    # Step 1: Connect Google Drive
    st.header("Step 1: Connect Google Drive")
    
    if st.session_state.google_creds is None:
        creds = connect_google_drive()
        if creds:
            st.session_state.google_creds = creds
            st.rerun()
    else:
        st.success("✅ Google Drive connected!")
        
        if st.button("🔄 Reconnect Google Drive"):
            st.session_state.google_creds = None
            st.rerun()
    
    # Step 2: Fetch transcripts
    if st.session_state.google_creds:
        st.header("Step 2: Search for Transcripts")
        
        if not st.session_state.transcripts:
            # Search options
            st.subheader("Search Options")
            
            # Meeting Code input
            meeting_code = st.text_input(
                "Meeting Code (e.g., abc-mnop-xyz)",
                help="Enter the Google Meet meeting code to search for specific transcripts",
                placeholder="abc-mnop-xyz"
            )
            
            # Date range inputs
            st.subheader("Time Range (Optional)")
            use_date_range = st.checkbox("Filter by date range", help="Enable to filter transcripts by modification date")
            
            start_datetime_str = None
            end_datetime_str = None
            
            if use_date_range:
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", key="start_date")
                    start_time = st.time_input("Start Time", value=datetime.time.min, key="start_time")
                with col2:
                    end_date = st.date_input("End Date", key="end_date")
                    end_time = st.time_input("End Time", value=datetime.time.max, key="end_time")
                
                # Convert dates to RFC3339 format for Google Drive API (UTC timezone)
                if start_date:
                    start_datetime = datetime.datetime.combine(start_date, start_time)
                    # Google Drive API expects UTC timezone, so we'll use local time but format as if UTC
                    # In production, you might want to convert from local timezone to UTC
                    start_datetime_str = start_datetime.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                
                if end_date:
                    end_datetime = datetime.datetime.combine(end_date, end_time)
                    end_datetime_str = end_datetime.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
            
            # Validate inputs
            if not meeting_code and not use_date_range:
                st.info("💡 Enter a meeting code OR enable date range filter to search for transcripts.")
            
            if st.button("📂 Search Transcripts"):
                try:
                    transcripts = fetch_transcripts(
                        st.session_state.google_creds,
                        meeting_code=meeting_code.strip() if meeting_code else None,
                        start_date=start_datetime_str,
                        end_date=end_datetime_str
                    )
                    # Only rerun if we found transcripts to show the selector
                    # If empty list or error, stay on search form to show messages
                    st.session_state.transcripts = transcripts
                    if transcripts:  # Only rerun if we have transcripts to display
                        st.rerun()
                except Exception as e:
                    # Error message already displayed in fetch_transcripts/list_drive_files
                    # Don't rerun on error so the error message stays visible
                    pass
        else:
            # Display transcript selector
            st.subheader("Select Transcript")
            transcript_names = [f"{t['name']} (Modified: {t.get('modifiedTime', 'Unknown')})" for t in st.session_state.transcripts]
            
            selected_idx = st.selectbox(
                "Choose a transcript to process:",
                range(len(transcript_names)),
                format_func=lambda x: transcript_names[x]
            )
            
            # Button to search again
            if st.button("🔍 New Search"):
                st.session_state.transcripts = []
                st.rerun()
            
            if st.button("📄 Load Transcript"):
                selected_file = st.session_state.transcripts[selected_idx]
                st.session_state.selected_transcript = selected_file
                
                # Load transcript content
                content = get_transcript_content(selected_file['id'], st.session_state.google_creds)
                st.session_state.transcript_content = content
                
                st.success(f"Loaded: {selected_file['name']}")
                st.text_area("Transcript Preview", content[:500] + "..." if len(content) > 500 else content, height=200)
    
    # Step 3: Process transcript with Gemini
    if st.session_state.transcript_content:
        st.header("Step 3: Extract Action Items")
        
        if st.button("🤖 Process with Gemini"):
            # Clean and process transcript
            cleaned_text = clean_transcript(st.session_state.transcript_content)
            action_items = extract_action_items(cleaned_text)
            
            if action_items:
                st.session_state.action_items = action_items
                st.success(f"✅ Extracted {len(action_items)} action item(s)")
                st.rerun()
            else:
                st.warning("No action items found in the transcript.")
    
    # Step 4: Display Kanban board
    if st.session_state.action_items:
        st.header("Step 4: Kanban Board")
        
        # Display summary
        display_tasks_summary(st.session_state.action_items)
        st.markdown("---")
        
        # Display Kanban board
        display_kanban_board(st.session_state.action_items)
        
        # Step 5: Save to Supabase
        st.markdown("---")
        st.header("Step 5: Save Tasks")
        
        user = get_user_session()
        if user and st.button("💾 Save to Supabase"):
            if save_tasks(user.id, st.session_state.action_items):
                st.success("✅ Tasks saved to Supabase!")
            else:
                st.error("❌ Failed to save tasks.")
        
        # Option to clear and start over
        if st.button("🔄 Clear & Start Over"):
            st.session_state.action_items = []
            st.session_state.transcript_content = None
            st.session_state.selected_transcript = None
            st.rerun()


if __name__ == "__main__":
    main()

