"""
Security Module

This module handles JWT token creation/verification and password hashing
using bcrypt for secure authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ============================================================================
# Password Hashing Configuration
# ============================================================================

# Create bcrypt context for password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Number of rounds for bcrypt (higher = more secure but slower)
)

# ============================================================================
# Token Constants
# ============================================================================

ALGORITHM = settings.algorithm
SECRET_KEY = settings.secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


# ============================================================================
# Password Hashing Functions
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Hashed password
        
    Example:
        hashed = hash_password("my_secure_password")
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        is_valid = verify_password("my_password", hashed_password)
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Functions
# ============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing token claims (e.g., {"sub": "user_id"})
        expires_delta: Optional custom expiration time. If not provided,
                      uses ACCESS_TOKEN_EXPIRE_MINUTES from settings
                      
    Returns:
        str: Encoded JWT token
        
    Example:
        token = create_access_token({"sub": "user_123"})
        token_with_custom_expiry = create_access_token(
            {"sub": "user_123"},
            expires_delta=timedelta(hours=2)
        )
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    # Encode JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary containing token claims (e.g., {"sub": "user_id"})
        expires_delta: Optional custom expiration time. If not provided,
                      uses REFRESH_TOKEN_EXPIRE_DAYS from settings
                      
    Returns:
        str: Encoded JWT refresh token
        
    Example:
        refresh_token = create_refresh_token({"sub": "user_123"})
    """
    to_encode = data.copy()
    
    # Set expiration time (longer than access token)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({"exp": expire})
    
    # Encode JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Optional[Dict[str, Any]]: Decoded token payload if valid, None if invalid
        
    Raises:
        JWTError: If token is invalid or expired
        
    Example:
        payload = verify_token(token)
        if payload:
            user_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"Token verification failed: {e}")
        return None


def get_token_subject(token: str) -> Optional[str]:
    """
    Extract the subject (user_id) from a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Optional[str]: Subject (user_id) if token is valid, None otherwise
        
    Example:
        user_id = get_token_subject(token)
    """
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None


def is_token_expired(token: str) -> bool:
    """
    Check if a JWT token is expired.
    
    Args:
        token: JWT token to check
        
    Returns:
        bool: True if token is expired, False otherwise
        
    Example:
        if is_token_expired(token):
            # Request new token
    """
    payload = verify_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    return datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc)


def create_token_pair(user_id: str) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User ID to include in tokens
        
    Returns:
        Dict[str, str]: Dictionary with "access_token" and "refresh_token"
        
    Example:
        tokens = create_token_pair("user_123")
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
    """
    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# ============================================================================
# Token Validation Utilities
# ============================================================================

def validate_token_format(token: str) -> bool:
    """
    Validate basic JWT token format (has 3 parts separated by dots).
    
    Args:
        token: Token to validate
        
    Returns:
        bool: True if token has valid format, False otherwise
        
    Example:
        if validate_token_format(token):
            # Token has valid format
    """
    if not token or not isinstance(token, str):
        return False
    
    parts = token.split(".")
    return len(parts) == 3


def extract_bearer_token(auth_header: str) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        Optional[str]: Extracted token if valid format, None otherwise
        
    Example:
        token = extract_bearer_token("Bearer eyJhbGc...")
    """
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


# ============================================================================
# Security Utilities
# ============================================================================

def generate_secure_random_string(length: int = 32) -> str:
    """
    Generate a secure random string for tokens or secrets.
    
    Args:
        length: Length of the random string
        
    Returns:
        str: Secure random string
        
    Example:
        secret = generate_secure_random_string(32)
    """
    import secrets
    return secrets.token_urlsafe(length)


async def get_current_user_optional(token: str, db_session) -> Optional[Dict[str, Any]]:
    """
    Get current user from token if valid, otherwise return None.
    
    Args:
        token: JWT token string
        db_session: Database session (needed for user lookup)
        
    Returns:
        Optional[Dict[str, Any]]: User data if token is valid, None otherwise
    """
    if not token:
        return None
    
    # Verify and decode token
    payload = verify_token(token)
    if not payload:
        return None
    
    # Extract user ID from token
    user_id: str = payload.get("sub")
    if not user_id:
        return None
    
    # For now, just return the user_id since we don't have db access here
    # In a real implementation, you'd look up the user in the database
    return {"id": user_id, "is_authenticated": True}
