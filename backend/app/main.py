"""
XTeam Backend Application

Main FastAPI application entry point with all configurations,
middleware, and route registrations.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket
import uvicorn

from app.core.config import settings
from app.core.database import init_db, get_db
from app.api.v1.api import api_router
from app.websocket.connection_manager import connection_manager
from app.core.security import get_current_user_optional
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import LoggingMiddleware, setup_json_logging
from app.middleware.rate_limit import RateLimitMiddleware
from app.models.user import User

# Configure structured JSON logging
setup_json_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    logger.info("Starting XTeam Backend...")

    # Startup: Initialize token blacklist service
    from app.core.token_blacklist import token_blacklist
    await token_blacklist.connect()

    # Startup: Create database tables
    await init_db()

    logger.info("Database tables created/verified")
    logger.info("XTeam Backend started successfully")

    yield

    # Shutdown: Clean up resources
    logger.info("Shutting down XTeam Backend...")
    await connection_manager.disconnect_all()
    logger.info("All WebSocket connections closed")
    
    # Shutdown: Disconnect token blacklist
    await token_blacklist.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Agent Platform for AI-assisted Software Development",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# ============================================================================
# Middleware Configuration
# ============================================================================

# Request ID Middleware - Must be first to set request ID for all requests
app.add_middleware(RequestIDMiddleware)

# Logging Middleware - Logs all requests with request IDs
app.add_middleware(LoggingMiddleware)

# Rate Limiting Middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_requests_per_minute
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Trusted Host Middleware (for production)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure properly for production
    )

# ============================================================================
# Static Files
# ============================================================================

# Mount static files directory if it exists
import os
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# ============================================================================
# Route Registration
# ============================================================================

# Include API v1 routes
app.include_router(
    api_router,
    prefix="/api/v1",
    tags=["API v1"],
)

# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Main WebSocket endpoint for real-time communication.

    Handles connection, authentication, and message routing.
    Requires valid JWT token for authentication.
    """
    # Extract token from query parameters
    token = websocket.query_params.get("token")
    
    if not token:
        # Reject connection without token
        await websocket.close(code=1008, reason="Authentication required")
        logger.warning("WebSocket connection rejected: No token provided")
        return
    
    # Verify token and get user
    from app.core.security import verify_token
    from app.core.token_blacklist import token_blacklist
    from sqlalchemy import select
    
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid or expired token")
        logger.warning("WebSocket connection rejected: Invalid token")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        logger.warning("WebSocket connection rejected: Invalid token payload")
        return
    
    # Check if token is revoked
    if await token_blacklist.is_token_revoked(token):
        await websocket.close(code=1008, reason="Token has been revoked")
        logger.warning(f"WebSocket connection rejected: Revoked token for user {user_id}")
        return
    
    # Check if all user tokens are revoked
    if await token_blacklist.is_user_tokens_revoked(user_id):
        await websocket.close(code=1008, reason="All user tokens revoked")
        logger.warning(f"WebSocket connection rejected: All tokens revoked for user {user_id}")
        return
    
    # Fetch user from database
    from app.core.database import get_db
    async for db in get_db():
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await websocket.close(code=1008, reason="User not found or inactive")
            logger.warning(f"WebSocket connection rejected: User {user_id} not found or inactive")
            return
        
        break
    
    try:
        # Accept connection
        await websocket.accept()

        # Register connection with authenticated user
        connection_id = await connection_manager.connect(websocket, user)

        logger.info(f"WebSocket connection established: {connection_id} for user {user_id}")

        try:
            # Main message loop
            while True:
                # Receive message
                data = await websocket.receive_json()

                # Process message through connection manager
                await connection_manager.handle_message(connection_id, data)

        except Exception as e:
            logger.error(f"WebSocket error for connection {connection_id}: {e}")

        finally:
            # Disconnect
            await connection_manager.disconnect(connection_id)
            logger.info(f"WebSocket connection closed: {connection_id}")

    except Exception as e:
        logger.error(f"WebSocket connection failed: {e}")


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/healthz")
async def health_liveness() -> dict:
    """
    Lightweight liveness probe for Kubernetes/load balancers.
    
    Returns basic application status without external dependencies check.
    This endpoint should always return 200 OK if the application is running.
    """
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/readyz")
async def health_readiness() -> JSONResponse:
    """
    Readiness probe with database and Redis connectivity checks.
    
    Returns 200 OK only if all critical dependencies are healthy.
    Used by orchestrators to determine if the service can receive traffic.
    """
    import time
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {},
    }
    
    all_healthy = True
    
    # Check database connection
    try:
        async for db in get_db():
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "ok"
            break
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = f"error: {str(e)}"
        all_healthy = False
    
    # Check Redis connection
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["checks"]["redis"] = f"error: {str(e)}"
        all_healthy = False
    
    health_status["status"] = "healthy" if all_healthy else "unhealthy"
    health_status["duration_ms"] = round((time.time() - start_time) * 1000, 2)
    
    status_code = 200 if all_healthy else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/health")
async def health_check() -> dict:
    """
    Legacy health check endpoint for backwards compatibility.
    
    Returns basic application status.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.

    Logs the error and returns a generic error response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred" if not settings.debug else str(exc),
        },
    )


# ============================================================================
# Startup
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
