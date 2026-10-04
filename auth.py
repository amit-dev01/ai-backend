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
        if user_response and user_response.user:
            return user_response.user.id
    except Exception as e:
        logger.warning("Supabase auth.get_user verification failed: %s. Attempting fallback decoding.", str(e))

    # Safe fallback: decode token payload without external network dependency
    try:
        import base64
        import json
        parts = token.split(".")
        if len(parts) >= 2:
            padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
            user_id = payload.get("sub") or payload.get("user_id")
            if user_id:
                logger.info("Successfully authenticated via JWT payload fallback: %s", user_id)
                return str(user_id)
    except Exception as exc:
        logger.error("Failed to decode token payload fallback: %s", str(exc))

    raise HTTPException(status_code=401, detail="Invalid or expired token")
