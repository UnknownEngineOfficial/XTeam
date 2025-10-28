"""
Project Schemas

This module defines Pydantic models for project-related API requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ProjectStatusEnum(str, Enum):
    """Project status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


# ============================================================================
# Project Creation and Update
# ============================================================================

class ProjectCreate(BaseModel):
    """
    Schema for project creation.
    
    Attributes:
        name: Project name
        description: Project description
        requirements: Project requirements/specifications
        repository_url: Optional Git repository URL
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Project name"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Project description"
    )
    requirements: Optional[str] = Field(
        None,
        max_length=5000,
        description="Project requirements/specifications"
    )
    repository_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional Git repository URL"
    )

    @validator("name")
    def validate_name(cls, v):
        """Validate project name."""
        if not v or not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()

    @validator("repository_url")
    def validate_repository_url(cls, v):
        """Validate repository URL format."""
        if v and not (v.startswith("http://") or v.startswith("https://") or v.startswith("git@")):
            raise ValueError("Repository URL must be a valid HTTP(S) or Git URL")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "AI Chat Application",
                "description": "A multi-agent AI chat application",
                "requirements": "Build a chat app with real-time messaging",
                "repository_url": "https://github.com/user/ai-chat"
            }
        }


class ProjectUpdate(BaseModel):
    """
    Schema for project update.
    
    Attributes:
        name: Project name
        description: Project description
        requirements: Project requirements
        repository_url: Git repository URL
        status: Project status
        progress: Project progress (0-100)
    """
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Project name"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Project description"
    )
    requirements: Optional[str] = Field(
        None,
        max_length=5000,
        description="Project requirements"
    )
    repository_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Git repository URL"
    )
    status: Optional[ProjectStatusEnum] = Field(
        None,
        description="Project status"
    )
    progress: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Project progress (0-100)"
    )

    @validator("progress")
    def validate_progress(cls, v):
        """Validate progress value."""
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Progress must be between 0 and 100")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "Updated Project Name",
                "description": "Updated description",
                "progress": 50.0,
                "status": "active"
            }
        }


# ============================================================================
# Execution Response Schemas (Nested)
# ============================================================================

class ExecutionSummary(BaseModel):
    """
    Schema for execution summary (nested in project response).
    
    Attributes:
        id: Execution ID
        execution_type: Type of execution
        status: Execution status
        started_at: Start timestamp
        completed_at: Completion timestamp
        duration_seconds: Duration in seconds
        error_message: Error message if failed
    """
    id: str = Field(..., description="Execution ID")
    execution_type: str = Field(..., description="Type of execution")
    status: str = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ExecutionDetail(ExecutionSummary):
    """
    Schema for detailed execution response.
    
    Extends ExecutionSummary with:
        agent_logs: Agent execution logs
        output: Execution output
        retry_count: Number of retries
    """
    agent_logs: List[Dict[str, Any]] = Field(default=[], description="Agent logs")
    output: Dict[str, Any] = Field(default={}, description="Execution output")
    retry_count: int = Field(..., description="Number of retries")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


# ============================================================================
# Project Response Schemas
# ============================================================================

class ProjectResponse(BaseModel):
    """
    Schema for project response.
    
    Attributes:
        id: Project ID
        owner_id: Owner user ID
        name: Project name
        description: Project description
        status: Project status
        workspace_path: Workspace path
        repository_url: Repository URL
        progress: Project progress
        created_at: Creation timestamp
        updated_at: Update timestamp
        started_at: Start timestamp
        completed_at: Completion timestamp
    """
    id: str = Field(..., description="Project ID")
    owner_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    status: str = Field(..., description="Project status")
    workspace_path: str = Field(..., description="Workspace path")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    progress: float = Field(..., description="Project progress (0-100)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "owner_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "AI Chat Application",
                "description": "A multi-agent AI chat application",
                "status": "active",
                "workspace_path": "/workspaces/XTeam/backend/workspaces/project_123",
                "repository_url": "https://github.com/user/ai-chat",
                "progress": 45.5,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T15:45:00Z",
                "started_at": "2024-01-15T11:00:00Z",
                "completed_at": None
            }
        }


class ProjectDetailResponse(ProjectResponse):
    """
    Schema for detailed project response with owner and execution history.
    
    Extends ProjectResponse with:
        owner: Owner user information
        requirements: Project requirements
        metadata: Project metadata
        executions: List of recent executions
    """
    owner: Optional[Dict[str, Any]] = Field(None, description="Owner user information")
    requirements: Optional[str] = Field(None, description="Project requirements")
    metadata: Dict[str, Any] = Field(default={}, description="Project metadata")
    executions: List[ExecutionSummary] = Field(default=[], description="Recent executions")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ProjectListResponse(BaseModel):
    """
    Schema for project list response.
    
    Attributes:
        total: Total number of projects
        page: Current page number
        page_size: Number of projects per page
        projects: List of project responses
    """
    total: int = Field(..., description="Total number of projects")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of projects per page")
    projects: List[ProjectResponse] = Field(..., description="List of projects")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total": 25,
                "page": 1,
                "page_size": 10,
                "projects": []
            }
        }


# ============================================================================
# Project Action Schemas
# ============================================================================

class ProjectStartRequest(BaseModel):
    """
    Schema for project start request.
    
    Attributes:
        execution_type: Type of execution (full, partial, test, deployment)
    """
    execution_type: str = Field(
        default="full",
        description="Type of execution"
    )

    @validator("execution_type")
    def validate_execution_type(cls, v):
        """Validate execution type."""
        valid_types = ["full", "partial", "test", "deployment"]
        if v not in valid_types:
            raise ValueError(f"Execution type must be one of {valid_types}")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "execution_type": "full"
            }
        }


class ProjectStatusUpdate(BaseModel):
    """
    Schema for project status update.
    
    Attributes:
        status: New project status
        reason: Optional reason for status change
    """
    status: ProjectStatusEnum = Field(..., description="New project status")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional reason for status change"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "paused",
                "reason": "Waiting for user feedback"
            }
        }


class ProjectProgressUpdate(BaseModel):
    """
    Schema for project progress update.
    
    Attributes:
        progress: Progress value (0-100)
        message: Optional progress message
    """
    progress: float = Field(
        ...,
        ge=0,
        le=100,
        description="Progress value (0-100)"
    )
    message: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional progress message"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "progress": 75.0,
                "message": "Code generation in progress"
            }
        }


# ============================================================================
# Project Statistics Schemas
# ============================================================================

class ProjectStats(BaseModel):
    """
    Schema for project statistics.
    
    Attributes:
        total_projects: Total number of projects
        active_projects: Number of active projects
        completed_projects: Number of completed projects
        failed_projects: Number of failed projects
        total_executions: Total number of executions
        successful_executions: Number of successful executions
        failed_executions: Number of failed executions
        average_duration: Average execution duration
    """
    total_projects: int = Field(..., description="Total number of projects")
    active_projects: int = Field(..., description="Number of active projects")
    completed_projects: int = Field(..., description="Number of completed projects")
    failed_projects: int = Field(..., description="Number of failed projects")
    total_executions: int = Field(..., description="Total number of executions")
    successful_executions: int = Field(..., description="Number of successful executions")
    failed_executions: int = Field(..., description="Number of failed executions")
    average_duration: Optional[float] = Field(None, description="Average execution duration")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total_projects": 15,
                "active_projects": 3,
                "completed_projects": 10,
                "failed_projects": 2,
                "total_executions": 45,
                "successful_executions": 40,
                "failed_executions": 5,
                "average_duration": 125.5
            }
        }


# ============================================================================
# Project Filter Schemas
# ============================================================================

class ProjectFilterParams(BaseModel):
    """
    Schema for project filtering parameters.
    
    Attributes:
        status: Filter by status
        search: Search by name or description
        sort_by: Sort field (created_at, updated_at, name, progress)
        sort_order: Sort order (asc, desc)
        page: Page number
        page_size: Items per page
    """
    status: Optional[ProjectStatusEnum] = Field(None, description="Filter by status")
    search: Optional[str] = Field(
        None,
        max_length=100,
        description="Search by name or description"
    )
    sort_by: str = Field(
        default="created_at",
        description="Sort field"
    )
    sort_order: str = Field(
        default="desc",
        description="Sort order (asc, desc)"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")

    @validator("sort_by")
    def validate_sort_by(cls, v):
        """Validate sort field."""
        valid_fields = ["created_at", "updated_at", "name", "progress"]
        if v not in valid_fields:
            raise ValueError(f"Sort field must be one of {valid_fields}")
        return v

    @validator("sort_order")
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "active",
                "search": "chat",
                "sort_by": "created_at",
                "sort_order": "desc",
                "page": 1,
                "page_size": 10
            }
        }


# ============================================================================
# Error Response Schemas
# ============================================================================

class ProjectErrorResponse(BaseModel):
    """
    Schema for project error response.
    
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
                "error": "Project not found",
                "detail": "Project with ID 550e8400-e29b-41d4-a716-446655440000 does not exist",
                "status_code": 404
            }
        }
