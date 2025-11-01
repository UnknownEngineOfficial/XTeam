"""
API Dependencies

This module defines FastAPI dependency functions for authentication, database access,
and other common request requirements.
"""

import time
import threading
from typing import Optional, Generator, AsyncGenerator
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_token, extract_bearer_token
from app.models.user import User

# ============================================================================
# Security Scheme
# ============================================================================

security = HTTPBearer(
    scheme_name="Bearer",
    description="JWT Bearer token authentication",
    auto_error=False,
)


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token in Authorization header.
    
    This dependency extracts the JWT token from the Authorization header,
    verifies it, and returns the associated User object from the database.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: 401 Unauthorized if token is missing, invalid, or expired
        HTTPException: 404 Not Found if user does not exist
        
    Example:
        @app.get("/me")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return current_user
    """
    # Check if credentials are provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Verify token format
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify and decode token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from token
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (convenience wrapper).
    
    This is a convenience dependency that ensures the user is active.
    It's essentially the same as get_current_user but with explicit naming.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: The active user
        
    Raises:
        HTTPException: 403 Forbidden if user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify they are a superuser.
    
    This dependency ensures the current user has superuser/admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: The superuser
        
    Raises:
        HTTPException: 403 Forbidden if user is not a superuser
        
    Example:
        @app.delete("/users/{user_id}")
        async def delete_user(
            user_id: str,
            admin: User = Depends(get_current_superuser)
        ):
            # Only superusers can delete users
            ...
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can access this resource",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    
    This dependency allows endpoints to work with or without authentication.
    
    Args:
        credentials: HTTP Bearer credentials (optional)
        db: Database session
        
    Returns:
        Optional[User]: The authenticated user or None
        
    Example:
        @app.get("/projects")
        async def list_projects(user: Optional[User] = Depends(get_optional_user)):
            if user:
                # Return user's projects
            else:
                # Return public projects
    """
    if not credentials:
        return None
    
    token = credentials.credentials
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
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    return user if user and user.is_active else None


# ============================================================================
# Database Dependencies
# ============================================================================

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.
    
    This is an alias for get_db() for explicit naming in some contexts.
    
    Yields:
        AsyncSession: Database session
    """
    async with get_db() as session:
        yield session


# ============================================================================
# Query Parameter Dependencies
# ============================================================================

class PaginationParams:
    """
    Pagination parameters dependency.
    
    Attributes:
        page: Page number (default: 1)
        page_size: Items per page (default: 10, max: 100)
    """
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 10,
    ):
        """
        Initialize pagination parameters.
        
        Args:
            page: Page number (must be >= 1)
            page_size: Items per page (must be 1-100)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100
        
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size
        self.limit = page_size


def get_pagination(
    page: int = 1,
    page_size: int = 10,
) -> PaginationParams:
    """
    Get pagination parameters from query string.
    
    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: 10, max: 100)
        
    Returns:
        PaginationParams: Pagination parameters
        
    Example:
        @app.get("/items")
        async def list_items(
            pagination: PaginationParams = Depends(get_pagination)
        ):
            skip = pagination.skip
            limit = pagination.limit
    """
    return PaginationParams(page=page, page_size=page_size)


class SortParams:
    """
    Sort parameters dependency.
    
    Attributes:
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)
    """
    
    def __init__(
        self,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        """
        Initialize sort parameters.
        
        Args:
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
        """
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        
        # Validate sort order
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "desc"


def get_sort(
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> SortParams:
    """
    Get sort parameters from query string.
    
    Args:
        sort_by: Field to sort by (default: created_at)
        sort_order: Sort order (default: desc)
        
    Returns:
        SortParams: Sort parameters
        
    Example:
        @app.get("/items")
        async def list_items(
            sort: SortParams = Depends(get_sort)
        ):
            # Use sort.sort_by and sort.sort_order
    """
    return SortParams(sort_by=sort_by, sort_order=sort_order)


# ============================================================================
# Search Dependencies
# ============================================================================

class SearchParams:
    """
    Search parameters dependency.
    
    Attributes:
        query: Search query string
        fields: Fields to search in
    """
    
    def __init__(
        self,
        q: Optional[str] = None,
        fields: Optional[str] = None,
    ):
        """
        Initialize search parameters.
        
        Args:
            q: Search query
            fields: Comma-separated list of fields to search
        """
        self.query = q or ""
        self.fields = [f.strip() for f in fields.split(",")] if fields else []


def get_search(
    q: Optional[str] = None,
    fields: Optional[str] = None,
) -> SearchParams:
    """
    Get search parameters from query string.
    
    Args:
        q: Search query
        fields: Comma-separated fields to search
        
    Returns:
        SearchParams: Search parameters
        
    Example:
        @app.get("/items")
        async def search_items(
            search: SearchParams = Depends(get_search)
        ):
            # Use search.query and search.fields
    """
    return SearchParams(q=q, fields=fields)


# ============================================================================
# Filter Dependencies
# ============================================================================

class FilterParams:
    """
    Filter parameters dependency.
    
    Attributes:
        filters: Dictionary of filter parameters
    """
    
    def __init__(self, **kwargs):
        """
        Initialize filter parameters.
        
        Args:
            **kwargs: Filter parameters
        """
        self.filters = {k: v for k, v in kwargs.items() if v is not None}


def get_filters(
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> FilterParams:
    """
    Get filter parameters from query string.
    
    Args:
        status: Filter by status
        is_active: Filter by active status
        
    Returns:
        FilterParams: Filter parameters
        
    Example:
        @app.get("/items")
        async def list_items(
            filters: FilterParams = Depends(get_filters)
        ):
            # Use filters.filters dictionary
    """
    return FilterParams(status=status, is_active=is_active)


# ============================================================================
# Rate Limiting Dependencies
# ============================================================================

class RateLimitStore:
    """
    Thread-safe rate limit store using singleton pattern.
    
    For production, replace with Redis implementation.
    """
    _instance = None
    _lock = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._store = {}
            # Use threading.Lock for thread safety
            cls._lock = threading.Lock()
        return cls._instance
    
    def get_requests(self, user_id: str) -> list:
        """Get request timestamps for a user."""
        with self._lock:
            return self._store.get(user_id, []).copy()
    
    def set_requests(self, user_id: str, timestamps: list) -> None:
        """Set request timestamps for a user."""
        with self._lock:
            self._store[user_id] = timestamps
    
    def add_request(self, user_id: str, timestamp: float) -> None:
        """Add a request timestamp for a user."""
        with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []
            self._store[user_id].append(timestamp)


async def check_rate_limit(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Check rate limit for current user.
    
    This dependency enforces rate limiting on specific endpoints using
    a thread-safe in-memory store. For production with multiple workers,
    use Redis-based rate limiting.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: The current user
        
    Raises:
        HTTPException: 429 Too Many Requests if rate limit exceeded
        
    Example:
        @app.post("/execute")
        async def execute_project(
            user: User = Depends(check_rate_limit)
        ):
            # This endpoint is rate limited
    """
    # Get rate limit store (singleton)
    rate_store = RateLimitStore()
    
    user_id = str(current_user.id)
    current_time = time.time()
    
    # Rate limit: 60 requests per minute per user
    window_seconds = 60
    max_requests = 60
    
    # Get current requests and clean up old entries
    requests = rate_store.get_requests(user_id)
    requests = [ts for ts in requests if current_time - ts < window_seconds]
    
    # Check rate limit
    if len(requests) >= max_requests:
        # Calculate retry time
        oldest_request = min(requests)
        retry_after = int(window_seconds - (current_time - oldest_request)) + 1
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    
    # Add current request and update store
    requests.append(current_time)
    rate_store.set_requests(user_id, requests)
    
    return current_user


# ============================================================================
# Validation Dependencies
# ============================================================================

async def validate_request_body(
    content_length: Optional[int] = Header(None),
) -> None:
    """
    Validate request body size.
    
    This dependency checks that the request body doesn't exceed maximum size.
    
    Args:
        content_length: Content-Length header value
        
    Raises:
        HTTPException: 413 Payload Too Large if body is too large
    """
    max_size = settings.max_upload_size_mb * 1024 * 1024
    
    if content_length and content_length > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body exceeds maximum size of {settings.max_upload_size_mb}MB",
        )


# ============================================================================
# Health Check Dependencies
# ============================================================================

async def check_database_health(
    db: AsyncSession = Depends(get_db),
) -> bool:
    """
    Check if database connection is healthy.
    
    This dependency can be used for health check endpoints.
    
    Args:
        db: Database session
        
    Returns:
        bool: True if database is healthy
        
    Raises:
        HTTPException: 503 Service Unavailable if database is unhealthy
    """
    try:
        # Simple health check query
        await db.execute(select(1))
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )
