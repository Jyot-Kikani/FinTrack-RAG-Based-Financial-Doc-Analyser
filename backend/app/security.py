# backend/app/security.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client

from . import config

# OAuth2 scheme for extracting Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_supabase_client() -> Client:
    """
    Creates a Supabase client instance.
    This is done inside a function to avoid initialization during module import.
    """
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not configured")

    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency that validates a Supabase JWT and returns the authenticated user.
    """
    try:
        supabase_client = get_supabase_client()

        # Validate the token using Supabase Auth
        user_response = supabase_client.auth.get_user(token)

        if not user_response or not user_response.user:
            raise Exception("Invalid session token")

        return user_response.user

    except Exception as e:
        print(f"Supabase Authentication Error: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )