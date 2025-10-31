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

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    logger.info("Starting XTeam Backend...")

    # Startup: Create database tables
    await init_db()

    logger.info("Database tables created/verified")
    logger.info("XTeam Backend started successfully")

    yield

    # Shutdown: Clean up resources
    logger.info("Shutting down XTeam Backend...")
    await connection_manager.disconnect_all()
    logger.info("All WebSocket connections closed")


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
    """
    try:
        # Accept connection
        await websocket.accept()

        # Try to authenticate user (optional for some connections)
        user = None
        try:
            token = websocket.query_params.get("token")
            if token:
                user = await get_current_user_optional(token, None)  # db not needed for basic auth
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")

        # Register connection
        connection_id = await connection_manager.connect(websocket, user)

        logger.info(f"WebSocket connection established: {connection_id}")

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
# Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint for load balancers and monitoring.

    Returns basic application status.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/health/detailed")
async def detailed_health_check() -> dict:
    """
    Detailed health check with database and Redis connectivity.

    Returns comprehensive system status.
    """
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {},
    }

    try:
        # Check database connection
        async for db in get_db():
            await db.execute("SELECT 1")
            health_status["checks"]["database"] = "ok"
            break
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Add more checks here (Redis, external services, etc.)

    return health_status


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
