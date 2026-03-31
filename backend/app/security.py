print("SECURITY MODULE IMPORTED")

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import json
import base64

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    Decodes the JWT payload locally to extract the user ID without network calls.
    The actual signature validation is deferred to Supabase API calls.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
            
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        
        payload_json = base64.urlsafe_b64decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing 'sub' claim")
            
        return user_id

    except Exception as e:
        print("Token decode error:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )