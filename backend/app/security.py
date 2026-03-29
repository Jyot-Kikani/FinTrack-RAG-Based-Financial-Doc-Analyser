# backend/app/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from gotrue import User

from . import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

supabase_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to verify JWT visually using Supabase's native API.
    """
    try:
        # Supabase's auth service natively handles all Base64, Audience, and Signature math.
        # This calls the GoTrue server directly to validate the session securely.
        user_response = supabase_client.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise Exception("Invalid session token")
            
        return user_response.user

    except Exception as e:
        print(f"Supabase Authentication Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )