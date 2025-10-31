"""
User Schemas

This module defines Pydantic models for user-related API requests and responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


# ============================================================================
# User Creation and Authentication
# ============================================================================

class UserCreate(BaseModel):
    """
    Schema for user registration/creation.
    
    Attributes:
        email: User email address
        username: User username
        password: User password (min 8 characters)
        full_name: Optional user full name
    """
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Username (3-50 chars, alphanumeric, underscore, hyphen)"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password (min 8 characters)"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User full name"
    )

    @validator("password")
    def validate_password(cls, v):
        """
        Validate password strength.
        
        Password must contain:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "password": "SecurePass123",
                "full_name": "John Doe"
            }
        }


class UserLogin(BaseModel):
    """
    Schema for user login.
    
    Attributes:
        email: User email address
        password: User password
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class UserUpdate(BaseModel):
    """
    Schema for user profile update.
    
    Attributes:
        full_name: User full name
        bio: User biography
        avatar_url: User avatar URL
    """
    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User full name"
    )
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="User biography"
    )
    avatar_url: Optional[str] = Field(
        None,
        max_length=500,
        description="User avatar URL"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "bio": "AI enthusiast and developer",
                "avatar_url": "https://example.com/avatar.jpg"
            }
        }


class PasswordChange(BaseModel):
    """
    Schema for password change.
    
    Attributes:
        old_password: Current password
        new_password: New password
    """
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="New password (min 8 characters)"
    )

    @validator("new_password")
    def validate_password(cls, v):
        """Validate new password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "old_password": "OldPass123",
                "new_password": "NewPass456"
            }
        }


# ============================================================================
# User Response Schemas
# ============================================================================

class UserResponse(BaseModel):
    """
    Schema for user response (public profile).
    
    Attributes:
        id: User ID
        email: User email
        username: User username
        full_name: User full name
        bio: User biography
        avatar_url: User avatar URL
        is_active: Whether user is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last login timestamp
    """
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="User username")
    full_name: Optional[str] = Field(None, description="User full name")
    bio: Optional[str] = Field(None, description="User biography")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
                "bio": "AI enthusiast",
                "avatar_url": "https://example.com/avatar.jpg",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T15:45:00Z",
                "last_login": "2024-01-20T15:45:00Z"
            }
        }


class UserDetailResponse(UserResponse):
    """
    Schema for detailed user response (includes admin info).
    
    Extends UserResponse with:
        is_superuser: Whether user is superuser
    """
    is_superuser: bool = Field(..., description="Whether user is superuser")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserListResponse(BaseModel):
    """
    Schema for user list response.
    
    Attributes:
        total: Total number of users
        page: Current page number
        page_size: Number of users per page
        users: List of user responses
    """
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of users per page")
    users: list[UserResponse] = Field(..., description="List of users")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total": 100,
                "page": 1,
                "page_size": 10,
                "users": []
            }
        }


# ============================================================================
# Token Schemas
# ============================================================================

class Token(BaseModel):
    """
    Schema for JWT token response.
    
    Attributes:
        access_token: JWT access token
        refresh_token: JWT refresh token
        token_type: Token type (bearer)
        expires_in: Token expiration time in seconds
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class TokenRefresh(BaseModel):
    """
    Schema for token refresh request.
    
    Attributes:
        refresh_token: JWT refresh token
    """
    refresh_token: str = Field(..., description="JWT refresh token")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenPayload(BaseModel):
    """
    Schema for JWT token payload.
    
    Attributes:
        sub: Subject (user ID)
        exp: Expiration time
        iat: Issued at time
    """
    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration time (Unix timestamp)")
    iat: int = Field(..., description="Issued at time (Unix timestamp)")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "sub": "550e8400-e29b-41d4-a716-446655440000",
                "exp": 1705761600,
                "iat": 1705758000
            }
        }


# ============================================================================
# Authentication Response Schemas
# ============================================================================

class LoginResponse(BaseModel):
    """
    Schema for login response.
    
    Attributes:
        user: User information
        token: Token information
    """
    user: UserResponse = Field(..., description="User information")
    token: Token = Field(..., description="Token information")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class RegisterResponse(BaseModel):
    """
    Schema for registration response.
    
    Attributes:
        user: Created user information
        token: Token information
        message: Success message
    """
    user: UserResponse = Field(..., description="Created user information")
    token: Token = Field(..., description="Token information")
    message: str = Field(default="User registered successfully", description="Success message")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


# ============================================================================
# Error Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Schema for error response.
    
    Attributes:
        error: Error message
        detail: Detailed error information
        status_code: HTTP status code
    """
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "Invalid credentials",
                "detail": "Email or password is incorrect",
                "status_code": 401
            }
        }


class ValidationErrorResponse(BaseModel):
    """
    Schema for validation error response.
    
    Attributes:
        error: Error message
        details: List of validation errors
        status_code: HTTP status code
    """
    error: str = Field(default="Validation error", description="Error message")
    details: list[dict] = Field(..., description="List of validation errors")
    status_code: int = Field(default=422, description="HTTP status code")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "Validation error",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format"
                    }
                ],
                "status_code": 422
            }
        }
