# ==============================================================================
# File: utils/security.py
# ==============================================================================

import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

# --- Configuration ---

# This is the correct variable name that matches your .env file.
# It reads the secret key that you invented.
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")

# A critical check to ensure the application doesn't start without the key.
if not APP_SECRET_KEY:
    # This error will stop the server if the key is missing in the environment,
    # preventing insecure operation.
    raise ValueError("FATAL ERROR: APP_SECRET_KEY environment variable is not set!")

# Defines that we expect the API key to be in the "Authorization" header.
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


# --- Dependency Function ---

async def get_api_key(api_key: str = Security(api_key_header)):
    """
    FastAPI dependency that validates the API key from the Authorization header.
    
    Checks for:
    1. Presence of the Authorization header.
    2. Correct format ("Bearer <your_key>").
    3. The key itself matches the one set in the environment.
    
    Raises HTTPException with a 401 status if any check fails.
    """
    # Check 1: Is the header missing?
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing.",
        )
        
    # Check 2: Does the header have the correct "Bearer " prefix?
    if not api_key.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Must be 'Bearer <token>'.",
        )
    
    # Extract the token part from the header string "Bearer <token>"
    token = api_key.split(" ")[1]
    
    # Check 3: Does the provided token match our secret key?
    if token == APP_SECRET_KEY:
        # If it matches, the request is authorized.
        return token
    else:
        # If it doesn't match, deny access.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key provided.",
        )