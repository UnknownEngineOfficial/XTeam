"""
Project Model

This module defines the Project ORM model for database persistence.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Text, DateTime, Index, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class Project(Base):
    """
    Project model representing AI development projects.
    
    Attributes:
        id: Unique project identifier (UUID)
        owner_id: User ID of project owner (FK to User)
        name: Project name
        description: Project description
        status: Project status (draft, active, paused, completed, archived, failed)
        workspace_path: Path to project workspace on filesystem
        repository_url: Optional Git repository URL
        requirements: Project requirements/specifications
        metadata: Additional project metadata (JSON)
        progress: Project completion progress (0-100)
        created_at: Project creation timestamp
        updated_at: Last project update timestamp
        started_at: Project start timestamp
        completed_at: Project completion timestamp
    """

    __tablename__ = "projects"

    # ========================================================================
    # Primary Key
    # ========================================================================

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        doc="Unique project identifier"
    )

    # ========================================================================
    # Foreign Keys
    # ========================================================================

    owner_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User ID of project owner"
    )

    # ========================================================================
    # Basic Information
    # ========================================================================

    name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Project name"
    )

    description = Column(
        Text,
        nullable=True,
        doc="Project description"
    )

    # ========================================================================
    # Project Status and Configuration
    # ========================================================================

    status = Column(
        Enum(ProjectStatus),
        default=ProjectStatus.DRAFT,
        nullable=False,
        index=True,
        doc="Project status"
    )

    workspace_path = Column(
        String(500),
        nullable=True,
        unique=True,
        doc="Path to project workspace on filesystem"
    )

    repository_url = Column(
        String(500),
        nullable=True,
        doc="Optional Git repository URL"
    )

    # ========================================================================
    # Project Details
    # ========================================================================

    requirements = Column(
        Text,
        nullable=True,
        doc="Project requirements/specifications"
    )

    project_metadata = Column(
        Text,
        default="{}",
        nullable=False,
        doc="Additional project metadata"
    )

    progress = Column(
        Float,
        default=0.0,
        nullable=False,
        doc="Project completion progress (0-100)"
    )

    # ========================================================================
    # Timestamp Fields
    # ========================================================================

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Project creation timestamp"
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Last project update timestamp"
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Project start timestamp"
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Project completion timestamp"
    )

    # ========================================================================
    # Relationships
    # ========================================================================

    # Relationship to owner (many projects belong to one user)
    owner = relationship(
        "User",
        back_populates="projects",
        foreign_keys=[owner_id],
        doc="Project owner"
    )

    # Relationship to executions (one project can have many executions)
    executions = relationship(
        "Execution",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="Execution.project_id",
        doc="Project executions"
    )

    # ========================================================================
    # Indexes
    # ========================================================================

    __table_args__ = (
        Index("idx_project_owner_id", "owner_id"),
        Index("idx_project_name", "name"),
        Index("idx_project_status", "status"),
        Index("idx_project_created_at", "created_at"),
        Index("idx_project_owner_status", "owner_id", "status"),
    )

    # ========================================================================
    # Methods
    # ========================================================================

    def __repr__(self) -> str:
        """String representation of Project."""
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"

    def __str__(self) -> str:
        """Project display name."""
        return self.name

    def to_dict(self, include_owner: bool = False) -> dict:
        """
        Convert project to dictionary.
        
        Args:
            include_owner: Whether to include owner information
            
        Returns:
            dict: Project data as dictionary
        """
        data = {
            "id": str(self.id),
            "owner_id": str(self.owner_id),
            "name": self.name,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "workspace_path": self.workspace_path,
            "repository_url": self.repository_url,
            "requirements": self.requirements,
            "metadata": self.project_metadata,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        
        if include_owner and self.owner:
            data["owner"] = {
                "id": str(self.owner.id),
                "username": self.owner.username,
                "email": self.owner.email,
                "full_name": self.owner.full_name,
            }
        
        return data

    def update_progress(self, progress: float) -> None:
        """
        Update project progress.
        
        Args:
            progress: Progress value (0-100)
            
        Raises:
            ValueError: If progress is not between 0 and 100
        """
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        self.progress = progress

    def start(self) -> None:
        """Mark project as started."""
        if self.status == ProjectStatus.DRAFT:
            self.status = ProjectStatus.ACTIVE
            self.started_at = datetime.now(timezone.utc)

    def pause(self) -> None:
        """Pause project execution."""
        if self.status == ProjectStatus.ACTIVE:
            self.status = ProjectStatus.PAUSED

    def resume(self) -> None:
        """Resume paused project."""
        if self.status == ProjectStatus.PAUSED:
            self.status = ProjectStatus.ACTIVE

    def complete(self) -> None:
        """Mark project as completed."""
        if self.status in [ProjectStatus.ACTIVE, ProjectStatus.PAUSED]:
            self.status = ProjectStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)
            self.progress = 100.0

    def fail(self, reason: Optional[str] = None) -> None:
        """
        Mark project as failed.
        
        Args:
            reason: Optional failure reason to store in metadata
        """
        self.status = ProjectStatus.FAILED
        if reason:
            if not self.project_metadata:
                self.project_metadata = {}
            self.project_metadata["failure_reason"] = reason

    def archive(self) -> None:
        """Archive project."""
        self.status = ProjectStatus.ARCHIVED

    def is_active(self) -> bool:
        """Check if project is currently active."""
        return self.status == ProjectStatus.ACTIVE

    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self.status == ProjectStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if project failed."""
        return self.status == ProjectStatus.FAILED

    def get_duration(self) -> Optional[float]:
        """
        Get project duration in seconds.
        
        Returns:
            Optional[float]: Duration in seconds if project has started, None otherwise
        """
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()

    def set_metadata(self, key: str, value) -> None:
        """
        Set metadata key-value pair.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        if not self.project_metadata:
            self.project_metadata = {}
        self.project_metadata[key] = value

    def get_metadata(self, key: str, default=None):
        """
        Get metadata value by key.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        if not self.project_metadata:
            return default
        return self.project_metadata.get(key, default)

    @classmethod
    def from_dict(cls, data: dict, owner_id: str) -> "Project":
        """
        Create Project instance from dictionary.
        
        Args:
            data: Dictionary with project data
            owner_id: Owner user ID
            
        Returns:
            Project: New Project instance
        """
        return cls(
            owner_id=owner_id,
            name=data.get("name"),
            description=data.get("description"),
            status=ProjectStatus(data.get("status", "draft")),
            workspace_path=data.get("workspace_path"),
            repository_url=data.get("repository_url"),
            requirements=data.get("requirements"),
            metadata=data.get("metadata", {}),
            progress=data.get("progress", 0.0),
        )
