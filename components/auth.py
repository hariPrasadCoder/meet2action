"""Supabase authentication components."""
import streamlit as st
from supabase import create_client
from utils.env_loader import get_supabase_url, get_supabase_key


def get_supabase_auth_client():
    """Get Supabase client for authentication."""
    url = get_supabase_url()
    key = get_supabase_key()
    return create_client(url, key)


def login_form():
    """
    Display login form and handle authentication.
    
    Returns:
        True if login successful, False otherwise
    """
    st.subheader("Login to Meet2Action")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            try:
                supabase = get_supabase_auth_client()
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    st.session_state.user = response.user
                    st.session_state.access_token = response.session.access_token
                    st.session_state.refresh_token = response.session.refresh_token
                    st.success("Login successful!")
                    st.rerun()
                    return True
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
                return False
    
    # Show sign up option
    with st.expander("Don't have an account? Sign up"):
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            signup_submit = st.form_submit_button("Sign Up")
            
            if signup_submit:
                try:
                    supabase = get_supabase_auth_client()
                    response = supabase.auth.sign_up({
                        "email": new_email,
                        "password": new_password
                    })
                    
                    if response.user:
                        st.success("Account created! Please check your email to verify your account.")
                except Exception as e:
                    st.error(f"Sign up failed: {str(e)}")
    
    return False


def logout_button():
    """Display logout button and handle logout."""
    if st.button("Logout"):
        try:
            supabase = get_supabase_auth_client()
            supabase.auth.sign_out()
            
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.success("Logged out successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Logout failed: {str(e)}")


def get_user_session():
    """
    Get current user session from Supabase.
    
    Returns:
        User object if logged in, None otherwise
    """
    try:
        supabase = get_supabase_auth_client()
        
        # Check if we have a session in state
        if 'access_token' in st.session_state:
            # Verify session is still valid
            try:
                user = supabase.auth.get_user(st.session_state.access_token)
                return user.user if user else None
            except:
                # Session expired, clear it
                if 'user' in st.session_state:
                    del st.session_state.user
                if 'access_token' in st.session_state:
                    del st.session_state.access_token
                if 'refresh_token' in st.session_state:
                    del st.session_state.refresh_token
                return None
        
        # Try to get session from Supabase
        session = supabase.auth.get_session()
        if session:
            st.session_state.user = session.user
            st.session_state.access_token = session.access_token
            st.session_state.refresh_token = session.refresh_token
            return session.user
        
        return None
    except Exception as e:
        return None


def is_logged_in() -> bool:
    """
    Check if user is logged in.
    
    Returns:
        True if logged in, False otherwise
    """
    user = get_user_session()
    return user is not None

