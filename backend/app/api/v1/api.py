"""
API v1 Router

Main API router that combines all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.agents import router as agents_router
from app.api.v1.websocket import router as websocket_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    projects_router,
    prefix="/projects",
    tags=["Projects"],
)

api_router.include_router(
    agents_router,
    prefix="/agents",
    tags=["Agents"],
)

api_router.include_router(
    websocket_router,
    prefix="/websocket",
    tags=["WebSocket"],
)