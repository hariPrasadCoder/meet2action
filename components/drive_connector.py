"""Google Drive connector for fetching Meet transcripts."""
import streamlit as st
from utils.google_auth import get_google_creds, list_drive_files, get_file_content
from utils.env_loader import get_google_client_id, get_google_client_secret
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


def connect_google_drive():
    """
    Connect to Google Drive and return credentials.
    
    Returns:
        Credentials object if successful, None otherwise
    """
    st.subheader("Connect Google Drive")
    
    creds = get_google_creds()
    
    if creds:
        st.success("✅ Google Drive connected!")
        return creds
    else:
        # Generate authorization URL
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": get_google_client_id(),
                        "client_secret": get_google_client_secret(),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost:8501"]
                    }
                },
                ['https://www.googleapis.com/auth/drive.readonly'],
                redirect_uri="http://localhost:8501"
            )
            
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            st.markdown(f"### 🔗 [Click here to authorize Google Drive access]({auth_url})")
            st.info("After authorizing, you'll be redirected back to the app.")
        except Exception as e:
            st.error(f"Error setting up Google Drive connection: {str(e)}")
        
        return None


def fetch_transcripts(creds: Credentials, meeting_code: str = None, start_date: str = None, end_date: str = None):
    """
    Fetch list of Google Meet transcripts from Drive, filtered by meeting code and/or date range.
    
    Args:
        creds: Google credentials
        meeting_code: Optional meeting code to search for (e.g., "abc-mnop-xyz")
        start_date: Optional start date/time in RFC3339 format
        end_date: Optional end date/time in RFC3339 format
        
    Returns:
        List of file dictionaries, or None on error
        
    Raises:
        ValueError: If credentials are not provided
        Exception: If there's an error fetching transcripts (error already displayed)
    """
    if not creds:
        raise ValueError("Please connect to Google Drive first.")
    
    with st.spinner("Searching for transcripts..."):
        files = list_drive_files(creds, meeting_code=meeting_code, start_date=start_date, end_date=end_date)
    
    # list_drive_files returns None on error, empty list on no files found
    if files is None:
        # Error occurred (error message already displayed in list_drive_files)
        # Raise exception so caller knows not to rerun
        raise Exception("Failed to fetch transcripts. See error message above.")
    
    if files:
        st.success(f"✅ Found {len(files)} transcript(s)")
        return files
    else:
        st.warning("⚠️ No transcripts found matching your criteria.")
        if meeting_code:
            st.info(f"💡 No transcripts found with meeting code: {meeting_code}")
        if start_date or end_date:
            st.info("💡 Try adjusting the date range or removing date filters.")
        return []


def get_transcript_content(file_id: str, creds: Credentials) -> str:
    """
    Get content of a specific transcript file.
    
    Args:
        file_id: Google Drive file ID
        creds: Google credentials
        
    Returns:
        Transcript content as string
    """
    if not creds:
        return ""
    
    with st.spinner("Loading transcript..."):
        content = get_file_content(file_id, creds)
    
    return content

