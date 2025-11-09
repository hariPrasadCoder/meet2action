"""Environment variable loader using python-dotenv."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env(key: str, default: str = None) -> str:
    """Get environment variable value."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} is not set")
    return value


def get_supabase_url() -> str:
    """Get Supabase URL from environment."""
    return get_env("SUPABASE_URL")


def get_supabase_key() -> str:
    """Get Supabase key from environment."""
    return get_env("SUPABASE_KEY")


def get_google_client_id() -> str:
    """Get Google Client ID from environment."""
    return get_env("GOOGLE_CLIENT_ID")


def get_google_client_secret() -> str:
    """Get Google Client Secret from environment."""
    return get_env("GOOGLE_CLIENT_SECRET")


def get_gemini_api_key() -> str:
    """Get Gemini API key from environment."""
    return get_env("GEMINI_API_KEY")

