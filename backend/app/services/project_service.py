"""
Project Service

This module provides business logic for project management including
CRUD operations and project-related utilities.
"""

from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectStats,
    ProjectFilterParams,
)
from app.models.execution import Execution, ExecutionStatus


# ============================================================================
# Project Service Class
# ============================================================================

class ProjectService:
    """
    Service class for project management.
    
    Provides CRUD operations and business logic for projects.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize project service.
        
        Args:
            db: Database session
        """
        self.db = db

    # ========================================================================
    # Create Operations
    # ========================================================================

    async def create_project(
        self,
        user_id: str,
        project_data: ProjectCreate,
        workspace_path: str,
    ) -> ProjectResponse:
        """
        Create a new project.
        
        Args:
            user_id: Owner user ID
            project_data: Project creation data
            workspace_path: Path to project workspace
            
        Returns:
            ProjectResponse: Created project
            
        Raises:
            ValueError: If workspace path already exists
        """
        # Check if workspace path already exists
        result = await self.db.execute(
            select(Project).where(Project.workspace_path == workspace_path)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"Workspace path already exists: {workspace_path}")
        
        # Create new project
        new_project = Project(
            owner_id=user_id,
            name=project_data.name,
            description=project_data.description,
            requirements=project_data.requirements,
            repository_url=project_data.repository_url,
            workspace_path=workspace_path,
            status=ProjectStatus.DRAFT,
            progress=0.0,
        )
        
        # Save to database
        self.db.add(new_project)
        await self.db.commit()
        await self.db.refresh(new_project)
        
        return ProjectResponse.from_attributes(new_project)

    # ========================================================================
    # Read Operations
    # ========================================================================

    async def get_project(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        include_executions: bool = False,
    ) -> Optional[ProjectDetailResponse]:
        """
        Get a project by ID.
        
        Args:
            project_id: Project ID
            user_id: Optional user ID for permission check
            include_executions: Whether to include execution history
            
        Returns:
            Optional[ProjectDetailResponse]: Project details or None if not found
            
        Raises:
            PermissionError: If user is not the owner and not admin
        """
        # Build query
        query = select(Project).where(Project.id == project_id)
        
        if include_executions:
            query = query.options(selectinload(Project.executions))
        
        query = query.options(selectinload(Project.owner))
        
        # Execute query
        result = await self.db.execute(query)
        project = result.unique().scalar_one_or_none()
        
        if not project:
            return None
        
        # Check permissions
        if user_id and str(project.owner_id) != user_id:
            # Check if user is admin (would need to fetch user)
            # For now, only allow owner access
            raise PermissionError("You do not have permission to access this project")
        
        # Convert to response
        response = ProjectDetailResponse.from_attributes(project)
        
        # Add execution history if requested
        if include_executions and project.executions:
            from app.schemas.project import ExecutionSummary
            response.executions = [
                ExecutionSummary.from_attributes(exec)
                for exec in project.executions[-10:]  # Last 10 executions
            ]
        
        return response

    async def get_project_by_owner(
        self,
        project_id: str,
        owner_id: str,
    ) -> Optional[Project]:
        """
        Get a project by ID and verify ownership.
        
        Args:
            project_id: Project ID
            owner_id: Expected owner ID
            
        Returns:
            Optional[Project]: Project if found and owned by user, None otherwise
        """
        result = await self.db.execute(
            select(Project).where(
                and_(
                    Project.id == project_id,
                    Project.owner_id == owner_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        user_id: Optional[str] = None,
        filters: Optional[ProjectFilterParams] = None,
    ) -> ProjectListResponse:
        """
        List projects with optional filtering.
        
        Args:
            user_id: Optional user ID to filter by owner
            filters: Optional filter parameters
            
        Returns:
            ProjectListResponse: Paginated list of projects
        """
        # Default filters
        if not filters:
            filters = ProjectFilterParams()
        
        # Build base query
        query = select(Project)
        
        # Apply filters
        if user_id:
            query = query.where(Project.owner_id == user_id)
        
        if filters.status:
            query = query.where(Project.status == ProjectStatus(filters.status.value))
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term),
                )
            )
        
        # Count total
        count_result = await self.db.execute(
            select(func.count(Project.id)).select_from(Project).where(
                query.whereclause if hasattr(query, 'whereclause') else True
            )
        )
        total = count_result.scalar() or 0
        
        # Apply sorting
        if filters.sort_by == "created_at":
            sort_column = Project.created_at
        elif filters.sort_by == "updated_at":
            sort_column = Project.updated_at
        elif filters.sort_by == "name":
            sort_column = Project.name
        elif filters.sort_by == "progress":
            sort_column = Project.progress
        else:
            sort_column = Project.created_at
        
        if filters.sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Apply pagination
        query = query.offset(filters.skip).limit(filters.limit)
        
        # Execute query
        result = await self.db.execute(query)
        projects = result.scalars().all()
        
        # Convert to responses
        project_responses = [
            ProjectResponse.from_attributes(p) for p in projects
        ]
        
        return ProjectListResponse(
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            projects=project_responses,
        )

    async def get_user_projects(
        self,
        user_id: str,
        filters: Optional[ProjectFilterParams] = None,
    ) -> ProjectListResponse:
        """
        Get all projects owned by a user.
        
        Args:
            user_id: User ID
            filters: Optional filter parameters
            
        Returns:
            ProjectListResponse: Paginated list of user's projects
        """
        return await self.list_projects(user_id=user_id, filters=filters)

    # ========================================================================
    # Update Operations
    # ========================================================================

    async def update_project(
        self,
        project_id: str,
        owner_id: str,
        update_data: ProjectUpdate,
    ) -> ProjectResponse:
        """
        Update a project.
        
        Args:
            project_id: Project ID
            owner_id: Owner user ID (for permission check)
            update_data: Update data
            
        Returns:
            ProjectResponse: Updated project
            
        Raises:
            PermissionError: If user is not the owner
            ValueError: If project not found
        """
        # Get project and verify ownership
        project = await self.get_project_by_owner(project_id, owner_id)
        if not project:
            raise ValueError(f"Project not found or access denied: {project_id}")
        
        # Update fields
        if update_data.name is not None:
            project.name = update_data.name
        
        if update_data.description is not None:
            project.description = update_data.description
        
        if update_data.requirements is not None:
            project.requirements = update_data.requirements
        
        if update_data.repository_url is not None:
            project.repository_url = update_data.repository_url
        
        if update_data.status is not None:
            project.status = ProjectStatus(update_data.status.value)
        
        if update_data.progress is not None:
            project.update_progress(update_data.progress)
        
        # Save changes
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        
        return ProjectResponse.from_attributes(project)

    async def update_project_status(
        self,
        project_id: str,
        owner_id: str,
        status: ProjectStatus,
    ) -> ProjectResponse:
        """
        Update project status.
        
        Args:
            project_id: Project ID
            owner_id: Owner user ID
            status: New status
            
        Returns:
            ProjectResponse: Updated project
            
        Raises:
            ValueError: If project not found
        """
        project = await self.get_project_by_owner(project_id, owner_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        project.status = status
        
        # Handle status-specific logic
        if status == ProjectStatus.ACTIVE:
            project.start()
        elif status == ProjectStatus.COMPLETED:
            project.complete()
        elif status == ProjectStatus.PAUSED:
            project.pause()
        elif status == ProjectStatus.FAILED:
            project.fail()
        elif status == ProjectStatus.ARCHIVED:
            project.archive()
        
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        
        return ProjectResponse.from_attributes(project)

    async def update_project_progress(
        self,
        project_id: str,
        owner_id: str,
        progress: float,
    ) -> ProjectResponse:
        """
        Update project progress.
        
        Args:
            project_id: Project ID
            owner_id: Owner user ID
            progress: Progress value (0-100)
            
        Returns:
            ProjectResponse: Updated project
            
        Raises:
            ValueError: If project not found or progress invalid
        """
        project = await self.get_project_by_owner(project_id, owner_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        project.update_progress(progress)
        
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        
        return ProjectResponse.from_attributes(project)

    # ========================================================================
    # Delete Operations
    # ========================================================================

    async def delete_project(
        self,
        project_id: str,
        owner_id: str,
    ) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: Project ID
            owner_id: Owner user ID (for permission check)
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            PermissionError: If user is not the owner
        """
        # Get project and verify ownership
        project = await self.get_project_by_owner(project_id, owner_id)
        if not project:
            return False
        
        # Delete project (cascades to executions)
        await self.db.delete(project)
        await self.db.commit()
        
        return True

    # ========================================================================
    # Statistics Operations
    # ========================================================================

    async def get_user_stats(self, user_id: str) -> ProjectStats:
        """
        Get project statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            ProjectStats: User's project statistics
        """
        # Count projects by status
        total_projects = await self._count_projects(user_id=user_id)
        active_projects = await self._count_projects(
            user_id=user_id,
            status=ProjectStatus.ACTIVE,
        )
        completed_projects = await self._count_projects(
            user_id=user_id,
            status=ProjectStatus.COMPLETED,
        )
        failed_projects = await self._count_projects(
            user_id=user_id,
            status=ProjectStatus.FAILED,
        )
        
        # Count executions
        total_executions = await self._count_executions(user_id=user_id)
        successful_executions = await self._count_executions(
            user_id=user_id,
            status=ExecutionStatus.COMPLETED,
        )
        failed_executions = await self._count_executions(
            user_id=user_id,
            status=ExecutionStatus.FAILED,
        )
        
        # Calculate average duration
        avg_duration = await self._get_average_execution_duration(user_id=user_id)
        
        return ProjectStats(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            failed_projects=failed_projects,
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            average_duration=avg_duration,
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _count_projects(
        self,
        user_id: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
    ) -> int:
        """
        Count projects with optional filters.
        
        Args:
            user_id: Optional user ID filter
            status: Optional status filter
            
        Returns:
            int: Number of projects
        """
        query = select(func.count(Project.id))
        
        if user_id:
            query = query.where(Project.owner_id == user_id)
        
        if status:
            query = query.where(Project.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _count_executions(
        self,
        user_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
    ) -> int:
        """
        Count executions with optional filters.
        
        Args:
            user_id: Optional user ID filter
            status: Optional status filter
            
        Returns:
            int: Number of executions
        """
        query = select(func.count(Execution.id))
        
        if user_id:
            query = query.join(Project).where(Project.owner_id == user_id)
        
        if status:
            query = query.where(Execution.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_average_execution_duration(
        self,
        user_id: Optional[str] = None,
    ) -> Optional[float]:
        """
        Get average execution duration.
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            Optional[float]: Average duration in seconds or None
        """
        query = select(func.avg(Execution.duration_seconds))
        
        if user_id:
            query = query.join(Project).where(Project.owner_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar()

    async def check_project_exists(self, project_id: str) -> bool:
        """
        Check if a project exists.
        
        Args:
            project_id: Project ID
            
        Returns:
            bool: True if project exists
        """
        result = await self.db.execute(
            select(func.count(Project.id)).where(Project.id == project_id)
        )
        return (result.scalar() or 0) > 0

    async def get_project_owner(self, project_id: str) -> Optional[str]:
        """
        Get the owner ID of a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Optional[str]: Owner ID or None if project not found
        """
        result = await self.db.execute(
            select(Project.owner_id).where(Project.id == project_id)
        )
        owner_id = result.scalar_one_or_none()
        return str(owner_id) if owner_id else None

    async def set_project_metadata(
        self,
        project_id: str,
        owner_id: str,
        key: str,
        value,
    ) -> ProjectResponse:
        """
        Set a metadata key-value pair for a project.
        
        Args:
            project_id: Project ID
            owner_id: Owner user ID
            key: Metadata key
            value: Metadata value
            
        Returns:
            ProjectResponse: Updated project
            
        Raises:
            ValueError: If project not found
        """
        project = await self.get_project_by_owner(project_id, owner_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        project.set_metadata(key, value)
        
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        
        return ProjectResponse.from_attributes(project)

    async def get_project_metadata(
        self,
        project_id: str,
        key: str,
        default=None,
    ):
        """
        Get a metadata value from a project.
        
        Args:
            project_id: Project ID
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        result = await self.db.execute(
            select(Project.metadata).where(Project.id == project_id)
        )
        metadata = result.scalar_one_or_none()
        
        if not metadata:
            return default
        
        return metadata.get(key, default)


# ============================================================================
# Service Factory Function
# ============================================================================

def get_project_service(db: AsyncSession) -> ProjectService:
    """
    Factory function to create a ProjectService instance.
    
    Args:
        db: Database session
        
    Returns:
        ProjectService: Service instance
    """
    return ProjectService(db)
