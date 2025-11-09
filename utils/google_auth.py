"""Google OAuth2 and Drive API helper functions."""
import os
from typing import List, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.env_loader import get_google_client_id, get_google_client_secret
import streamlit as st


# OAuth 2.0 scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_FILE = '.token.json'


def get_google_creds() -> Credentials:
    """
    Get Google credentials from token file or initiate OAuth flow.
    
    Returns:
        Credentials object or None if authentication fails
    """
    creds = None
    
    # Check if token file exists
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            # Token file is invalid, remove it
            os.remove(TOKEN_FILE)
    
    # If no valid credentials, initiate OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception:
                # Refresh failed, need to re-authenticate
                creds = None
        
        if not creds or not creds.valid:
            # Need to initiate OAuth flow
            query_params = st.query_params
            
            # Check if we have authorization code in URL
            if 'code' in query_params:
                # We have the code, exchange it for tokens
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
                        SCOPES,
                        redirect_uri="http://localhost:8501"
                    )
                    
                    code = query_params['code']
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    
                    # Save credentials for future use
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    
                    # Clear the code from URL
                    st.query_params.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Authentication failed: {str(e)}")
                    return None
            else:
                # Need to redirect to authorization
                return None
    
    return creds


def list_drive_files(creds: Credentials, meeting_code: str = None, start_date: str = None, end_date: str = None) -> List[Dict]:
    """
    List Google Drive files that are Meet transcripts, filtered by meeting code and/or date range.
    
    Args:
        creds: Google credentials
        meeting_code: Optional meeting code to search for (e.g., "abc-mnop-xyz")
        start_date: Optional start date/time in RFC3339 format (e.g., "2024-01-01T00:00:00Z")
        end_date: Optional end date/time in RFC3339 format (e.g., "2024-12-31T23:59:59Z")
        
    Returns:
        List of file dictionaries with id, name, and mimeType, or None on error
    """
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Build base query for Google Docs files
        query_parts = [
            "mimeType='application/vnd.google-apps.document'",
            "trashed=false"
        ]
        
        # Add meeting code filter if provided
        if meeting_code and meeting_code.strip():
            # Remove hyphens and search for the code (meeting codes might be in different formats)
            code_clean = meeting_code.strip().replace('-', '')
            # Search for the code in filename (with or without hyphens)
            query_parts.append(f"(name contains '{meeting_code}' or name contains '{code_clean}')")
        
        # Add date range filter if provided
        if start_date:
            query_parts.append(f"modifiedTime >= '{start_date}'")
        if end_date:
            query_parts.append(f"modifiedTime <= '{end_date}'")
        
        # Combine query parts
        query = " and ".join(query_parts)
        
        # Search for files (globally and in "Meet Recordings" folder)
        all_files = []
        seen_file_ids = set()
        
        # First, search globally
        try:
            results = service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, modifiedTime, mimeType)",
                orderBy="modifiedTime desc"
            ).execute()
            
            found_files = results.get('files', [])
            for file in found_files:
                if file['id'] not in seen_file_ids:
                    seen_file_ids.add(file['id'])
                    all_files.append(file)
        except Exception as e:
            st.warning(f"Global search failed: {str(e)}")
            # Continue to try folder search even if global search fails
        
        # Also search in "Meet Recordings" folder (especially important when meeting code is provided)
        # This ensures we find transcripts that are specifically in that folder
        if not all_files or meeting_code:
            try:
                # First, find the "Meet Recordings" folder
                folder_query = "name='Meet Recordings' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                folder_results = service.files().list(
                    q=folder_query,
                    pageSize=10,
                    fields="files(id, name)"
                ).execute()
                
                folders = folder_results.get('files', [])
                if folders:
                    folder_id = folders[0]['id']
                    # Build query for files in folder
                    folder_query_parts = [
                        f"'{folder_id}' in parents",
                        "mimeType='application/vnd.google-apps.document'",
                        "trashed=false"
                    ]
                    
                    # Add meeting code filter if provided
                    if meeting_code and meeting_code.strip():
                        code_clean = meeting_code.strip().replace('-', '')
                        meeting_code_filter = f"(name contains '{meeting_code}' or name contains '{code_clean}')"
                        folder_query_parts.append(meeting_code_filter)
                    
                    # Add date range filters if provided
                    if start_date:
                        folder_query_parts.append(f"modifiedTime >= '{start_date}'")
                    if end_date:
                        folder_query_parts.append(f"modifiedTime <= '{end_date}'")
                    
                    folder_query = " and ".join(folder_query_parts)
                    
                    folder_results = service.files().list(
                        q=folder_query,
                        pageSize=100,
                        fields="files(id, name, modifiedTime, mimeType)",
                        orderBy="modifiedTime desc"
                    ).execute()
                    
                    found_files = folder_results.get('files', [])
                    for file in found_files:
                        if file['id'] not in seen_file_ids:
                            seen_file_ids.add(file['id'])
                            all_files.append(file)
            except Exception as e:
                # Folder search is optional, continue if it fails
                # Only show warning if we haven't found any files yet
                if not all_files:
                    st.warning(f"Search in 'Meet Recordings' folder failed: {str(e)}")
                pass
        
        return all_files
    except HttpError as error:
        error_details = error.error_details[0] if error.error_details else {}
        error_reason = error_details.get('reason', 'unknown')
        error_message = error_details.get('message', str(error))
        
        # Display detailed error message
        if error.resp.status == 403:
            st.error(f"❌ Access Denied (403): {error_message}")
            st.error(f"Reason: {error_reason}")
            st.info("💡 Please ensure you have granted the necessary permissions to access Google Drive.")
        else:
            st.error(f"❌ Error fetching files: {error_message} (Status: {error.resp.status})")
        
        return None
    except Exception as error:
        st.error(f"❌ Unexpected error: {str(error)}")
        return None


def get_file_content(file_id: str, creds: Credentials) -> str:
    """
    Get content of a Google Docs file (transcript).
    
    Args:
        file_id: Google Drive file ID
        creds: Google credentials
        
    Returns:
        File content as text
    """
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Export as plain text
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        content = request.execute()
        
        return content.decode('utf-8')
    except HttpError as error:
        st.error(f"An error occurred: {error}")
        return ""

