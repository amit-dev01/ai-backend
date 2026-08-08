import logging
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import supabase_client

logger = logging.getLogger(__name__)
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    FastAPI dependency to extract the user ID from the Supabase JWT token.
    Uses Supabase Auth to validate the token.
    """
    if not supabase_client:
        # In case supabase client failed to initialize, mock user for local dev or raise error
        logger.warning("Supabase client not initialized, rejecting auth.")
        raise HTTPException(status_code=500, detail="Database connection not available")

    token = credentials.credentials
    try:
        user_response = supabase_client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return user_response.user.id
    except Exception as e:
        logger.error("Authentication error: %s", str(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")
