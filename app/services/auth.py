from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import logging
 
logger = logging.getLogger(__name__)
 
 
# ========== PASSWORD HASHING ==========
# CryptContext handles all bcrypt operations
# bcrypt automatically salts and hashes — never store plain passwords
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
 
def hash_password(plain_password: str) -> str:
    """
    Converts plain text password to bcrypt hash.
 
    EXAMPLE:
    "mypassword123" → "$2b$12$EixZaYVK1fsbw1ZfbX3OXe..."
 
    WHY BCRYPT?
    - Slow by design (makes brute force attacks expensive)
    - Automatically handles salting (prevents rainbow table attacks)
    - Industry standard for password storage
    """
    return pwd_context.hash(plain_password)
 
 
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain password matches a stored hash.
 
    EXAMPLE:
    verify_password("mypassword123", "$2b$12$EixZaYVK1fsbw1Z...") → True
    verify_password("wrongpassword", "$2b$12$EixZaYVK1fsbw1Z...") → False
 
    NOTE: Never compare plain text to hash directly — always use this function.
    """
    return pwd_context.verify(plain_password, hashed_password)
 
 
# ========== JWT TOKEN CREATION ==========
 
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a short-lived JWT access token.
 
    ACCESS TOKEN:
    - Short lived (default 30 minutes from settings)
    - Sent in every API request header: "Authorization: Bearer <token>"
    - Contains user identity (sub = subject = user_id)
 
    JWT STRUCTURE (3 parts separated by dots):
    Header.Payload.Signature
    - Header: algorithm used
    - Payload: your data (user_id, expiry) — NOT encrypted, just encoded
    - Signature: proves token wasn't tampered with
    """
    to_encode = data.copy()
 
    # Set expiration time
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
 
    to_encode.update({
        "exp": expire,          # Expiration time (JWT standard claim)
        "type": "access"        # Custom claim to distinguish token types
    })
 
    # Sign and encode the token
    token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
 
    return token
 
 
def create_refresh_token(data: dict) -> str:
    """
    Creates a long-lived JWT refresh token.
 
    REFRESH TOKEN:
    - Long lived (default 7 days from settings)
    - Stored securely by frontend (httpOnly cookie or secure storage)
    - Used ONLY to get new access tokens when they expire
    - Never sent to regular API endpoints
 
    WHY TWO TOKENS?
    - Access token: short life = less risk if stolen
    - Refresh token: long life = user stays logged in
    - If access token stolen: attacker has 30 min max
    - If refresh token stolen: user can logout to invalidate
    """
    to_encode = data.copy()
 
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
 
    to_encode.update({
        "exp": expire,
        "type": "refresh"       # Distinguish from access token
    })
 
    token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
 
    return token
 
 
# ========== JWT TOKEN VERIFICATION ==========
 
def verify_access_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT access token.
 
    RETURNS:
    - dict with payload (including 'sub' = user_id) if valid
    - None if token is expired, tampered, or invalid
 
    VALIDATES:
    ✅ Signature is correct (wasn't tampered)
    ✅ Token hasn't expired
    ✅ Token type is 'access' (not a refresh token)
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
 
        # Make sure this is an access token, not a refresh token
        if payload.get("type") != "access":
            logger.warning("Token type mismatch: expected access token")
            return None
 
        return payload
 
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
 
 
def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT refresh token.
 
    RETURNS:
    - dict with payload if valid
    - None if invalid
 
    Used in POST /auth/refresh to issue new access tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
 
        if payload.get("type") != "refresh":
            logger.warning("Token type mismatch: expected refresh token")
            return None
 
        return payload
 
    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {e}")
        return None
 
 
def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extracts user_id from a valid access token.
 
    SHORTCUT HELPER used in the get_current_user dependency.
    Returns None if token is invalid.
    """
    payload = verify_access_token(token)
    if payload:
        return payload.get("sub")   # 'sub' is JWT standard for subject (user id)
    return None