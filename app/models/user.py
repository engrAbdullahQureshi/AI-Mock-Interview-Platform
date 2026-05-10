from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
 
 
# ========== REQUEST MODELS ==========
# These define what the CLIENT sends TO the API
 
class UserRegisterRequest(BaseModel):
    """
    Data required to register a new user.
    Sent by frontend in POST /api/v1/auth/register
    """
    username: str = Field(
        ...,                        # ... means required (no default)
        min_length=3,
        max_length=50,
        description="Unique display name"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address (will be verified for format)"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (minimum 8 characters)"
    )
 
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }
 
 
class UserLoginRequest(BaseModel):
    """
    Data required to log in.
    Sent by frontend in POST /api/v1/auth/login
    """
    email: EmailStr
    password: str
 
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }
 
 
class TokenRefreshRequest(BaseModel):
    """
    Refresh token sent to get a new access token.
    Sent by frontend in POST /api/v1/auth/refresh
    """
    refresh_token: str
 
 
# ========== RESPONSE MODELS ==========
# These define what the API sends BACK to the client
 
class UserResponse(BaseModel):
    """
    User data returned to client.
    NOTE: Never includes password_hash!
    """
    id: str                         # MongoDB _id converted to string
    username: str
    email: str
    created_at: datetime
 
    class Config:
        json_schema_extra = {
            "example": {
                "id": "64f1a2b3c4d5e6f7a8b9c0d1",
                "username": "john_doe",
                "email": "john@example.com",
                "created_at": "2024-01-15T10:30:00"
            }
        }
 
 
class TokenResponse(BaseModel):
    """
    JWT tokens returned after successful login or register.
    Frontend stores these and sends access_token in Authorization header.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"      # Standard OAuth2 token type
    expires_in: int                 # Access token lifetime in seconds
    user: UserResponse              # User info so frontend doesn't need extra call
 
 
class MessageResponse(BaseModel):
    """
    Simple message response for operations like logout.
    """
    message: str
    success: bool = True
 
 
# ========== DATABASE MODEL ==========
# This represents how users are stored IN MongoDB
 
class UserInDB(BaseModel):
    """
    Full user document as stored in MongoDB.
    Never sent directly to client (contains password_hash).
 
    FLOW:
    Client sends UserRegisterRequest
    → We create UserInDB (adding password_hash, timestamps)
    → Store UserInDB in MongoDB
    → Return UserResponse (without password_hash) to client
    """
    username: str
    email: str
    password_hash: str              # bcrypt hashed password, NEVER plain text
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True          # Can be used to soft-ban users