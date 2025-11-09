"""Supabase client initialization and database operations."""
from supabase import create_client, Client
from utils.env_loader import get_supabase_url, get_supabase_key
from typing import List, Dict, Optional
import streamlit as st


def get_supabase_client(access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> Client:
    """
    Initialize and return Supabase client.
    
    Args:
        access_token: Optional access token for authenticated requests.
                     If not provided, will check session state.
        refresh_token: Optional refresh token for authenticated requests.
                      If not provided, will check session state.
    
    Returns:
        Supabase client instance
    """
    url = get_supabase_url()
    key = get_supabase_key()
    
    # Use tokens from parameters or session state for authenticated requests
    token = access_token or st.session_state.get('access_token')
    refresh = refresh_token or st.session_state.get('refresh_token')
    
    if token:
        # Create authenticated client with user's access token
        client = create_client(url, key)
        
        # Set the session to use the access token and refresh token
        # This ensures RLS policies can identify the authenticated user via auth.uid()
        if refresh:
            try:
                client.auth.set_session(access_token=token, refresh_token=refresh)
            except Exception:
                # If set_session fails, try setting just the access token
                try:
                    client.auth.set_session(access_token=token, refresh_token="")
                except Exception:
                    # Fallback: set Authorization header directly on postgrest client
                    if hasattr(client, 'postgrest') and hasattr(client.postgrest, 'auth'):
                        client.postgrest.auth(token)
        else:
            # No refresh token, try with empty string
            try:
                client.auth.set_session(access_token=token, refresh_token="")
            except Exception:
                # Fallback: set Authorization header directly
                if hasattr(client, 'postgrest') and hasattr(client.postgrest, 'auth'):
                    client.postgrest.auth(token)
        return client
    
    # Return unauthenticated client (uses anon key)
    return create_client(url, key)


def save_tasks(user_id: str, tasks_list: List[Dict], access_token: Optional[str] = None) -> bool:
    """
    Save tasks to Supabase tasks table.
    
    Args:
        user_id: Supabase user ID
        tasks_list: List of task dictionaries with keys: assignee, task, priority
        access_token: Optional access token for authenticated request
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get authenticated client using access token
        supabase = get_supabase_client(access_token=access_token)
        
        # Prepare tasks for insertion
        tasks_to_insert = []
        for task in tasks_list:
            tasks_to_insert.append({
                "user_id": user_id,
                "assignee": task.get("assignee", "Unassigned"),
                "task": task.get("task", ""),
                "priority": task.get("priority", "Medium")
            })
        
        # Insert tasks
        result = supabase.table("tasks").insert(tasks_to_insert).execute()
        return True
    except Exception as e:
        st.error(f"Error saving tasks: {str(e)}")
        return False


def fetch_tasks(user_id: str, access_token: Optional[str] = None) -> List[Dict]:
    """
    Fetch user's tasks from Supabase.
    
    Args:
        user_id: Supabase user ID
        access_token: Optional access token for authenticated request
        
    Returns:
        List of task dictionaries
    """
    try:
        # Get authenticated client using access token
        supabase = get_supabase_client(access_token=access_token)
        result = supabase.table("tasks").select("*").eq("user_id", user_id).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Error fetching tasks: {str(e)}")
        return []


def delete_task(task_id: str, access_token: Optional[str] = None) -> bool:
    """
    Delete a task by ID.
    
    Args:
        task_id: Task ID to delete
        access_token: Optional access token for authenticated request
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get authenticated client using access token
        supabase = get_supabase_client(access_token=access_token)
        supabase.table("tasks").delete().eq("id", task_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting task: {str(e)}")
        return False

