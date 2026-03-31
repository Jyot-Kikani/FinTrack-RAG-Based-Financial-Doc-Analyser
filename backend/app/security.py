print("SECURITY MODULE IMPORTED")

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client

from . import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_supabase_client():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return user_response.user

    except Exception as e:
        print("Supabase auth error:", e)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )