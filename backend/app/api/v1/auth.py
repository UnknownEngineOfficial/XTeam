"""
Authentication API Endpoints

This module defines FastAPI endpoints for user authentication including
registration, login, token refresh, and profile management.
"""

from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_token_pair,
    create_access_token,
)
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    PasswordChange,
    UserResponse,
    UserDetailResponse,
    Token,
    TokenRefresh,
    LoginResponse,
    RegisterResponse,
    ErrorResponse,
)
from app.api.deps import get_current_user, get_current_active_user

# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


# ============================================================================
# Registration Endpoint
# ============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, username, and password",
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """
    Register a new user account.
    
    This endpoint creates a new user account with the provided credentials.
    The password is hashed using bcrypt before storage.
    
    Args:
        user_data: User registration data (email, username, password, full_name)
        db: Database session
        
    Returns:
        RegisterResponse: Created user and authentication tokens
        
    Raises:
        HTTPException: 400 Bad Request if email or username already exists
        HTTPException: 422 Unprocessable Entity if validation fails
        
    Example:
        POST /api/v1/auth/register
        {
            "email": "user@example.com",
            "username": "john_doe",
            "password": "SecurePass123",
            "full_name": "John Doe"
        }
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
    )
    
    # Save user to database
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create tokens
    tokens = create_token_pair(str(new_user.id))
    
    # Convert to response
    user_response = UserResponse.from_attributes(new_user)
    token_response = Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=settings.access_token_expire_minutes * 60,
    )
    
    return RegisterResponse(
        user=user_response,
        token=token_response,
        message="User registered successfully",
    )


# ============================================================================
# Login Endpoint
# ============================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user with email and password",
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user and return tokens.
    
    This endpoint authenticates a user with email and password,
    and returns JWT access and refresh tokens.
    
    Args:
        credentials: Login credentials (email, password)
        db: Database session
        
    Returns:
        LoginResponse: User information and authentication tokens
        
    Raises:
        HTTPException: 401 Unauthorized if credentials are invalid
        HTTPException: 403 Forbidden if user account is inactive
        
    Example:
        POST /api/v1/auth/login
        {
            "email": "user@example.com",
            "password": "SecurePass123"
        }
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Update last login timestamp
    user.update_last_login()
    await db.commit()
    
    # Create tokens
    tokens = create_token_pair(str(user.id))
    
    # Convert to response
    user_response = UserResponse.from_attributes(user)
    token_response = Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=settings.access_token_expire_minutes * 60,
    )
    
    return LoginResponse(
        user=user_response,
        token=token_response,
    )


# ============================================================================
# Token Refresh Endpoint
# ============================================================================

@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using a refresh token",
)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Refresh access token using refresh token.
    
    This endpoint validates the refresh token and returns a new access token.
    
    Args:
        token_data: Token refresh request (refresh_token)
        db: Database session
        
    Returns:
        Token: New access token
        
    Raises:
        HTTPException: 401 Unauthorized if refresh token is invalid or expired
        HTTPException: 404 Not Found if user does not exist
        
    Example:
        POST /api/v1/auth/refresh
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    """
    from app.core.security import verify_token
    
    # Verify refresh token
    payload = verify_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Create new access token
    access_token = create_access_token({"sub": user_id})
    
    return Token(
        access_token=access_token,
        refresh_token=token_data.refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


# ============================================================================
# Profile Endpoints
# ============================================================================

@router.get(
    "/me",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserDetailResponse:
    """
    Get current user's profile information.
    
    This endpoint returns the profile of the currently authenticated user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserDetailResponse: User profile with admin information
        
    Raises:
        HTTPException: 401 Unauthorized if not authenticated
        
    Example:
        GET /api/v1/auth/me
        Authorization: Bearer <access_token>
    """
    return UserDetailResponse.from_attributes(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    description="Update the profile of the currently authenticated user",
)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update current user's profile information.
    
    This endpoint allows users to update their profile information
    such as full name, bio, and avatar URL.
    
    Args:
        profile_data: Updated profile data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserResponse: Updated user profile
        
    Raises:
        HTTPException: 401 Unauthorized if not authenticated
        
    Example:
        PUT /api/v1/auth/me
        Authorization: Bearer <access_token>
        {
            "full_name": "John Doe",
            "bio": "AI enthusiast",
            "avatar_url": "https://example.com/avatar.jpg"
        }
    """
    # Update user fields
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio
    
    if profile_data.avatar_url is not None:
        current_user.avatar_url = profile_data.avatar_url
    
    # Save changes
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.from_attributes(current_user)


# ============================================================================
# Password Management Endpoints
# ============================================================================

@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    description="Change the password of the currently authenticated user",
)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Change current user's password.
    
    This endpoint allows users to change their password by providing
    their current password and a new password.
    
    Args:
        password_data: Password change data (old_password, new_password)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 401 Unauthorized if old password is incorrect
        HTTPException: 400 Bad Request if new password is same as old
        
    Example:
        POST /api/v1/auth/change-password
        Authorization: Bearer <access_token>
        {
            "old_password": "OldPass123",
            "new_password": "NewPass456"
        }
    """
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    
    # Check if new password is different from old
    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )
    
    # Hash and update password
    current_user.hashed_password = hash_password(password_data.new_password)
    
    # Save changes
    db.add(current_user)
    await db.commit()
    
    return {"message": "Password changed successfully"}


# ============================================================================
# Logout Endpoint
# ============================================================================

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout the currently authenticated user",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Logout current user.
    
    This endpoint performs logout operations. Since we're using stateless JWT tokens,
    the actual logout is handled on the client side by discarding the tokens.
    This endpoint can be used for logging purposes or future session management.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
        
    Example:
        POST /api/v1/auth/logout
        Authorization: Bearer <access_token>
    """
    # TODO: Implement token blacklisting if needed
    # For now, logout is handled client-side by discarding tokens
    
    return {"message": "Logged out successfully"}


# ============================================================================
# Verification Endpoints
# ============================================================================

@router.get(
    "/verify-email/{token}",
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify user email address with verification token",
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify user email address.
    
    This endpoint verifies a user's email address using a verification token.
    
    Args:
        token: Email verification token
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 400 Bad Request if token is invalid or expired
        HTTPException: 404 Not Found if user not found
        
    Note:
        This is a placeholder for email verification functionality.
        Implementation depends on email service integration.
    """
    # TODO: Implement email verification logic
    # This would involve:
    # 1. Verifying the token
    # 2. Finding the user associated with the token
    # 3. Marking the user's email as verified
    
    return {"message": "Email verified successfully"}


@router.post(
    "/request-password-reset",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request a password reset token for email",
)
async def request_password_reset(
    email: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request password reset token.
    
    This endpoint sends a password reset token to the user's email address.
    
    Args:
        email: User email address
        db: Database session
        
    Returns:
        dict: Success message
        
    Note:
        This is a placeholder for password reset functionality.
        Implementation depends on email service integration.
    """
    # TODO: Implement password reset request logic
    # This would involve:
    # 1. Finding the user by email
    # 2. Generating a reset token
    # 3. Sending the token via email
    
    return {"message": "Password reset email sent"}


@router.post(
    "/reset-password/{token}",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset user password with reset token",
)
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reset user password.
    
    This endpoint resets a user's password using a password reset token.
    
    Args:
        token: Password reset token
        new_password: New password
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 400 Bad Request if token is invalid or expired
        HTTPException: 404 Not Found if user not found
        
    Note:
        This is a placeholder for password reset functionality.
        Implementation depends on email service integration.
    """
    # TODO: Implement password reset logic
    # This would involve:
    # 1. Verifying the reset token
    # 2. Finding the user associated with the token
    # 3. Updating the user's password
    
    return {"message": "Password reset successfully"}


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if authentication service is healthy",
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    This endpoint can be used to verify that the authentication service is running.
    
    Returns:
        dict: Health status
        
    Example:
        GET /api/v1/auth/health
    """
    return {"status": "healthy", "service": "authentication"}
