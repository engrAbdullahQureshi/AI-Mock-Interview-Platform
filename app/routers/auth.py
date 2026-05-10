from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
 
from app.database import get_database
from app.models.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
    UserInDB,
)
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_user_id_from_token,
)
from app.config import settings
import logging
 
logger = logging.getLogger(__name__)
 
# ========== ROUTER SETUP ==========
router = APIRouter()
 
# HTTPBearer extracts "Bearer <token>" from Authorization header automatically
security = HTTPBearer()
 
 
# ========== REUSABLE AUTH DEPENDENCY ==========
 
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> dict:
    """
    FastAPI dependency that protects routes requiring authentication.
 
    HOW TO USE ON ANY PROTECTED ROUTE:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            return {"message": f"Hello {current_user['username']}"}
 
    FLOW:
    1. Extracts Bearer token from Authorization header
    2. Verifies JWT signature and expiry
    3. Looks up user in MongoDB
    4. Returns user dict if valid, raises 401 if not
 
    RAISES:
    - 401 Unauthorized: if token missing, invalid, expired, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
 
    # Step 1: Extract user_id from token
    user_id = get_user_id_from_token(credentials.credentials)
    if not user_id:
        raise credentials_exception
 
    # Step 2: Look up user in database
    # Import here to avoid circular import issues
    from bson import ObjectId
 
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise credentials_exception
 
    if not user:
        raise credentials_exception
 
    # Step 3: Check user is active (not banned)
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact support."
        )
 
    return user
 
 
# ========== AUTH ENDPOINTS ==========
 
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    request: UserRegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Register a new user account.
 
    FLOW:
    1. Check email is not already taken
    2. Hash the password with bcrypt
    3. Save user to MongoDB
    4. Return JWT tokens (user is logged in immediately after registering)
 
    RETURNS: TokenResponse with access_token, refresh_token, and user info
    """
 
    # Step 1: Check if email already exists
    existing_user = await db.users.find_one({"email": request.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )
 
    # Also check username uniqueness
    existing_username = await db.users.find_one({"username": request.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken."
        )
 
    # Step 2: Hash password — NEVER store plain text
    hashed_pw = hash_password(request.password)
 
    # Step 3: Build the user document for MongoDB
    now = datetime.utcnow()
    user_doc = {
        "username": request.username,
        "email": request.email.lower(),     # Always store email lowercase
        "password_hash": hashed_pw,
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }
 
    # Step 4: Insert into MongoDB
    try:
        result = await db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        logger.info(f"New user registered: {request.email}")
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again."
        )
 
    # Step 5: Create JWT tokens
    token_data = {"sub": user_id}   # 'sub' = subject = user identifier
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
 
    # Step 6: Return tokens + user info
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user=UserResponse(
            id=user_id,
            username=request.username,
            email=request.email.lower(),
            created_at=now,
        )
    )
 
 
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(
    request: UserLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Authenticate a user and return JWT tokens.
 
    FLOW:
    1. Find user by email in MongoDB
    2. Verify the provided password against stored hash
    3. Return new JWT tokens
 
    SECURITY NOTE:
    We use the same error message for "user not found" and "wrong password"
    to prevent user enumeration attacks (attackers can't tell which is wrong).
    """
 
    # Generic error used for both "not found" and "wrong password"
    # This prevents attackers from knowing which is wrong
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )
 
    # Step 1: Find user by email
    user = await db.users.find_one({"email": request.email.lower()})
    if not user:
        raise auth_error
 
    # Step 2: Verify password against stored hash
    if not verify_password(request.password, user["password_hash"]):
        raise auth_error
 
    # Step 3: Check account is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact support."
        )
 
    # Step 4: Create JWT tokens
    user_id = str(user["_id"])
    token_data = {"sub": user_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
 
    logger.info(f"User logged in: {request.email}")
 
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user_id,
            username=user["username"],
            email=user["email"],
            created_at=user["created_at"],
        )
    )
 
 
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Get new access token using refresh token",
)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Issue a new access token using a valid refresh token.
 
    WHEN FRONTEND USES THIS:
    - Access token expires (after 30 min)
    - Frontend automatically calls this with stored refresh token
    - Gets new access token without forcing user to re-login
 
    FLOW:
    1. Verify refresh token is valid and not expired
    2. Look up user still exists in DB
    3. Return fresh access token + new refresh token
    """
    from bson import ObjectId
 
    invalid_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token. Please log in again.",
    )
 
    # Step 1: Verify refresh token
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise invalid_error
 
    user_id = payload.get("sub")
    if not user_id:
        raise invalid_error
 
    # Step 2: Confirm user still exists
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise invalid_error
 
    if not user or not user.get("is_active", True):
        raise invalid_error
 
    # Step 3: Issue fresh tokens
    token_data = {"sub": user_id}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
 
    logger.info(f"Tokens refreshed for user: {user['email']}")
 
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user_id,
            username=user["username"],
            email=user["email"],
            created_at=user["created_at"],
        )
    )
 
 
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout (stateless)",
)
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    Logout the current user.
 
    STATELESS LOGOUT:
    Since we're not using Redis, we can't blacklist the token server-side.
    The frontend is responsible for deleting the stored tokens on logout.
 
    This endpoint confirms the user was authenticated and signals the
    frontend to clear its stored tokens.
 
    WHAT FRONTEND MUST DO:
    1. Call this endpoint
    2. Delete access_token from memory
    3. Delete refresh_token from storage
    4. Redirect to login page
    """
    logger.info(f"User logged out: {current_user['email']}")
 
    return MessageResponse(
        message="Logged out successfully. Please delete your tokens.",
        success=True
    )
 
 
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged-in user info",
)
async def get_me(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the currently authenticated user's profile.
 
    USEFUL FOR:
    - Frontend to load user info on app startup
    - Verifying the token is still valid
 
    REQUIRES: Valid access token in Authorization header
    """
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        created_at=current_user["created_at"],
    )