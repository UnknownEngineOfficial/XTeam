"""
Projects API Endpoints

This module defines FastAPI endpoints for project management including
CRUD operations and project-related functionality.
"""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.project import ProjectStatus
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectStats,
    ProjectFilterParams,
    ProjectStatusUpdate,
    ProjectProgressUpdate,
    ProjectErrorResponse,
)
from app.services.project_service import ProjectService, get_project_service
from app.api.deps import (
    get_current_user,
    get_pagination,
    get_sort,
    PaginationParams,
    SortParams,
)

# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    responses={
        401: {"model": ProjectErrorResponse, "description": "Unauthorized"},
        403: {"model": ProjectErrorResponse, "description": "Forbidden"},
        404: {"model": ProjectErrorResponse, "description": "Not Found"},
        422: {"model": ProjectErrorResponse, "description": "Validation Error"},
        500: {"model": ProjectErrorResponse, "description": "Internal Server Error"},
    },
)


# ============================================================================
# List Projects Endpoint
# ============================================================================

@router.get(
    "",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="List user projects",
    description="Get a paginated list of projects owned by the current user",
)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
) -> ProjectListResponse:
    """
    List all projects owned by the current user.
    
    This endpoint returns a paginated list of projects with optional filtering
    and sorting capabilities.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        status_filter: Optional status filter (draft, active, paused, completed, archived, failed)
        search: Optional search term for name/description
        sort_by: Field to sort by (created_at, updated_at, name, progress)
        sort_order: Sort order (asc or desc)
        page: Page number (default: 1)
        page_size: Items per page (default: 10, max: 100)
        
    Returns:
        ProjectListResponse: Paginated list of projects
        
    Example:
        GET /api/v1/projects?page=1&page_size=10&sort_by=created_at&sort_order=desc
    """
    # Create filter parameters
    filters = ProjectFilterParams(
        status=status_filter,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    
    # Get service and list projects
    service = get_project_service(db)
    return await service.get_user_projects(str(current_user.id), filters=filters)


# ============================================================================
# Create Project Endpoint
# ============================================================================

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project with the provided details",
)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Create a new project.
    
    This endpoint creates a new project owned by the current user.
    A workspace directory is automatically created for the project.
    
    Args:
        project_data: Project creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProjectResponse: Created project
        
    Raises:
        HTTPException: 400 Bad Request if project creation fails
        
    Example:
        POST /api/v1/projects
        {
            "name": "AI Chat Application",
            "description": "A multi-agent AI chat app",
            "requirements": "Build a chat app with real-time messaging",
            "repository_url": "https://github.com/user/ai-chat"
        }
    """
    try:
        # Generate workspace path
        import uuid
        project_id = str(uuid.uuid4())
        workspace_path = os.path.join(
            settings.metagpt_workspace,
            str(current_user.id),
            project_id,
        )
        
        # Create workspace directory
        os.makedirs(workspace_path, exist_ok=True)
        
        # Create project
        service = get_project_service(db)
        project = await service.create_project(
            str(current_user.id),
            project_data,
            workspace_path,
        )
        
        return project
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )


# ============================================================================
# Get Project Endpoint
# ============================================================================

@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project details",
    description="Get detailed information about a specific project",
)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_executions: bool = Query(False, description="Include execution history"),
) -> ProjectDetailResponse:
    """
    Get detailed information about a project.
    
    This endpoint returns detailed information about a project including
    owner information, requirements, metadata, and optionally execution history.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
        include_executions: Whether to include execution history
        
    Returns:
        ProjectDetailResponse: Project details
        
    Raises:
        HTTPException: 404 Not Found if project not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        service = get_project_service(db)
        project = await service.get_project(
            project_id,
            user_id=str(current_user.id),
            include_executions=include_executions,
        )
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        return project
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project",
        )


# ============================================================================
# Update Project Endpoint
# ============================================================================

@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update project",
    description="Update project details",
)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Update a project.
    
    This endpoint allows updating project details such as name, description,
    requirements, repository URL, status, and progress.
    
    Args:
        project_id: Project ID
        update_data: Update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProjectResponse: Updated project
        
    Raises:
        HTTPException: 404 Not Found if project not found
        HTTPException: 403 Forbidden if user is not the owner
        HTTPException: 400 Bad Request if update fails
        
    Example:
        PATCH /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
        {
            "name": "Updated Project Name",
            "progress": 50.0,
            "status": "active"
        }
    """
    try:
        service = get_project_service(db)
        project = await service.update_project(
            project_id,
            str(current_user.id),
            update_data,
        )
        
        return project
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this project",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project",
        )


# ============================================================================
# Update Project Status Endpoint
# ============================================================================

@router.post(
    "/{project_id}/status",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update project status",
    description="Change the status of a project",
)
async def update_project_status(
    project_id: str,
    status_update: ProjectStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Update project status.
    
    This endpoint changes the status of a project and performs status-specific
    operations (e.g., starting, completing, pausing).
    
    Args:
        project_id: Project ID
        status_update: Status update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProjectResponse: Updated project
        
    Raises:
        HTTPException: 404 Not Found if project not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/status
        {
            "status": "active",
            "reason": "Starting project execution"
        }
    """
    try:
        service = get_project_service(db)
        project = await service.update_project_status(
            project_id,
            str(current_user.id),
            ProjectStatus(status_update.status.value),
        )
        
        return project
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project status",
        )


# ============================================================================
# Update Project Progress Endpoint
# ============================================================================

@router.post(
    "/{project_id}/progress",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update project progress",
    description="Update the progress of a project",
)
async def update_project_progress(
    project_id: str,
    progress_update: ProjectProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Update project progress.
    
    This endpoint updates the progress percentage of a project.
    
    Args:
        project_id: Project ID
        progress_update: Progress update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProjectResponse: Updated project
        
    Raises:
        HTTPException: 404 Not Found if project not found
        HTTPException: 403 Forbidden if user is not the owner
        HTTPException: 400 Bad Request if progress is invalid
        
    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/progress
        {
            "progress": 75.0,
            "message": "Code generation in progress"
        }
    """
    try:
        service = get_project_service(db)
        project = await service.update_project_progress(
            project_id,
            str(current_user.id),
            progress_update.progress,
        )
        
        return project
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project progress",
        )


# ============================================================================
# Delete Project Endpoint
# ============================================================================

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project and all associated data",
)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a project.
    
    This endpoint deletes a project and all associated data including
    executions and workspace files.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: 404 Not Found if project not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        DELETE /api/v1/projects/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        service = get_project_service(db)
        
        # Get project to find workspace path
        project = await service.get_project_by_owner(project_id, str(current_user.id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Delete project from database
        deleted = await service.delete_project(project_id, str(current_user.id))
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Delete workspace directory
        if project.workspace_path and os.path.exists(project.workspace_path):
            import shutil
            try:
                shutil.rmtree(project.workspace_path)
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to delete workspace directory: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project",
        )


# ============================================================================
# Project Statistics Endpoint
# ============================================================================

@router.get(
    "/stats/overview",
    response_model=ProjectStats,
    status_code=status.HTTP_200_OK,
    summary="Get project statistics",
    description="Get statistics about user's projects and executions",
)
async def get_project_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectStats:
    """
    Get project statistics for the current user.
    
    This endpoint returns statistics about the user's projects and executions
    including counts by status and average execution duration.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProjectStats: User's project statistics
        
    Example:
        GET /api/v1/projects/stats/overview
    """
    try:
        service = get_project_service(db)
        stats = await service.get_user_stats(str(current_user.id))
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )


# ============================================================================
# Project Metadata Endpoints
# ============================================================================

@router.post(
    "/{project_id}/metadata/{key}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Set project metadata",
    description="Set a metadata key-value pair for a project",
)
async def set_project_metadata(
    project_id: str,
    key: str,
    value: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Set project metadata.
    
    This endpoint sets a metadata key-value pair for a project.
    
    Args:
        project_id: Project ID
        key: Metadata key
        value: Metadata value
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ProjectResponse: Updated project
        
    Raises:
        HTTPException: 404 Not Found if project not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/metadata/custom_field
        {
            "data": "custom_value"
        }
    """
    try:
        service = get_project_service(db)
        project = await service.set_project_metadata(
            project_id,
            str(current_user.id),
            key,
            value,
        )
        
        return project
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set metadata",
        )


@router.get(
    "/{project_id}/metadata/{key}",
    status_code=status.HTTP_200_OK,
    summary="Get project metadata",
    description="Get a metadata value from a project",
)
async def get_project_metadata(
    project_id: str,
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get project metadata.
    
    This endpoint retrieves a metadata value from a project.
    
    Args:
        project_id: Project ID
        key: Metadata key
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Metadata value
        
    Raises:
        HTTPException: 404 Not Found if project not found
        HTTPException: 403 Forbidden if user is not the owner
        
    Example:
        GET /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/metadata/custom_field
    """
    try:
        service = get_project_service(db)
        
        # Verify project exists and user has access
        project = await service.get_project_by_owner(project_id, str(current_user.id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Get metadata
        value = await service.get_project_metadata(project_id, key)
        
        return {"key": key, "value": value}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metadata",
        )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if projects service is healthy",
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    This endpoint can be used to verify that the projects service is running.
    
    Returns:
        dict: Health status
        
    Example:
        GET /api/v1/projects/health
    """
    return {"status": "healthy", "service": "projects"}


# ============================================================================
# Execute Workflow Endpoint
# ============================================================================

@router.post(
    "/{project_id}/execute",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Execute workflow",
    description="Execute a MetaGPT workflow for the project",
)
async def execute_workflow(
    project_id: str,
    prompt: str = Query(..., description="Project requirements/prompt"),
    execution_type: str = Query("full", description="Execution type (full, incremental)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Execute a MetaGPT workflow for a project.
    
    This endpoint starts a MetaGPT workflow execution with all configured agents.
    The workflow runs asynchronously and streams updates via WebSocket.
    
    Args:
        project_id: Project ID
        prompt: Project requirements/prompt
        execution_type: Type of execution (full, incremental)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Execution details with execution ID
        
    Raises:
        HTTPException: 404 Not Found if project not found
        HTTPException: 403 Forbidden if user is not the owner
        HTTPException: 400 Bad Request if execution fails
        
    Example:
        POST /api/v1/projects/550e8400-e29b-41d4-a716-446655440000/execute?prompt=Build%20a%20REST%20API&execution_type=full
    """
    try:
        from app.models.execution import ExecutionType
        from app.metagpt_integration.agent_manager import get_agent_manager
        from app.metagpt_integration.streaming import get_streaming_handler
        
        # Verify project exists and user has access
        service = get_project_service(db)
        project = await service.get_project_by_owner(project_id, str(current_user.id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Parse execution type
        try:
            exec_type = ExecutionType(execution_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid execution type: {execution_type}",
            )
        
        # Get streaming handler for real-time updates
        streaming_handler = await get_streaming_handler()
        
        # Create agent manager
        agent_manager = await get_agent_manager(db, project, str(current_user.id))
        
        # Start workflow execution in background
        async def run_workflow():
            try:
                # Subscribe to streaming events for this execution
                subscriber_id = f"execution_{project_id}"
                await streaming_handler.subscribe(
                    subscriber_id=subscriber_id,
                    callback=lambda event: None,  # WebSocket will handle this
                    event_filter=None,
                )
                
                # Execute workflow
                async for update in agent_manager.run_workflow(prompt, exec_type):
                    # Emit event to streaming handler
                    await streaming_handler.emit(
                        event_type=update.get("type", "unknown"),
                        data=update,
                        source="workflow",
                        execution_id=update.get("execution_id"),
                        project_id=project_id,
                    )
                    
                    # Yield update for potential future use
                    yield update
                
                # Unsubscribe from streaming
                await streaming_handler.unsubscribe(subscriber_id)
                
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                await streaming_handler.emit(
                    event_type="error",
                    data={"error": str(e)},
                    source="workflow",
                    project_id=project_id,
                )
        
        # Start background task
        import asyncio
        asyncio.create_task(run_workflow())
        
        return {
            "message": "Workflow execution started",
            "project_id": project_id,
            "execution_type": execution_type,
            "status": "running",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start workflow execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start workflow execution",
        )
