"""
Request ID Middleware

Adds a unique request ID to each request for distributed tracing.
"""

import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from contextvars import ContextVar

# Context variable to store request ID across async contexts
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a unique request ID to each HTTP request.
    
    The request ID can be provided by the client via X-Request-ID header,
    or will be automatically generated as a UUID.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add request ID."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in context var for access in other parts of the app
        request_id_var.set(request_id)
        
        # Store in request state for easy access
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()
