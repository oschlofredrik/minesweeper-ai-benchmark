"""Simple authentication for the API."""

import os
import secrets
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Initialize security
security = HTTPBasic()

def get_auth_credentials() -> tuple[str, str]:
    """Get username and password from settings/environment."""
    from src.core.config import settings
    
    username = settings.auth_username
    password = settings.auth_password
    
    # Generate a secure default password if none is set
    if not password:
        password = secrets.token_urlsafe(16)
        print(f"⚠️  No AUTH_PASSWORD set. Using generated password: {password}")
        print("   Set AUTH_USERNAME and AUTH_PASSWORD environment variables to change.")
    
    return username, password

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify HTTP Basic Auth credentials."""
    correct_username, correct_password = get_auth_credentials()
    
    # Use secrets.compare_digest to prevent timing attacks
    is_valid_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        correct_username.encode("utf8")
    )
    is_valid_password = secrets.compare_digest(
        credentials.password.encode("utf8"), 
        correct_password.encode("utf8")
    )
    
    if not (is_valid_username and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

# Optional: Create a dependency that can be easily disabled
def get_current_user(enabled: bool = True):
    """Get current user with optional authentication."""
    from src.core.config import settings
    
    if enabled and not settings.disable_auth:
        return Depends(verify_credentials)
    else:
        # Return a dummy function that doesn't require auth
        async def no_auth():
            return "anonymous"
        return Depends(no_auth)