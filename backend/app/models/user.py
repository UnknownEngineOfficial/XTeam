"""
User Model

This module defines the User ORM model for database persistence.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class User(Base):
    """
    User model representing application users.
    
    Attributes:
        id: Unique user identifier (UUID)
        email: User email address (unique)
        username: User username (unique)
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        is_active: Whether user account is active
        is_superuser: Whether user has superuser privileges
        created_at: Account creation timestamp
        updated_at: Last account update timestamp
        last_login: Last login timestamp
        bio: User biography/description
        avatar_url: URL to user's avatar image
    """

    __tablename__ = "users"

    # ========================================================================
    # Primary Key
    # ========================================================================

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="Unique user identifier"
    )

    # ========================================================================
    # Authentication Fields
    # ========================================================================

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User email address"
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="User username"
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password"
    )

    # ========================================================================
    # Profile Fields
    # ========================================================================

    full_name = Column(
        String(255),
        nullable=True,
        doc="User's full name"
    )

    bio = Column(
        Text,
        nullable=True,
        doc="User biography/description"
    )

    avatar_url = Column(
        String(500),
        nullable=True,
        doc="URL to user's avatar image"
    )

    # ========================================================================
    # Status Fields
    # ========================================================================

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether user account is active"
    )

    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether user has superuser privileges"
    )

    # ========================================================================
    # Timestamp Fields
    # ========================================================================

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Account creation timestamp"
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Last account update timestamp"
    )

    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last login timestamp"
    )

    # ========================================================================
    # Relationships
    # ========================================================================

    # Relationship to projects (one user can have many projects)
    projects = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Project.owner_id",
        doc="Projects owned by this user"
    )

    # Relationship to executions (one user can have many executions)
    executions = relationship(
        "Execution",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Execution.user_id",
        doc="Executions created by this user"
    )

    # ========================================================================
    # Indexes
    # ========================================================================

    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_created_at", "created_at"),
    )

    # ========================================================================
    # Methods
    # ========================================================================

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

    def __str__(self) -> str:
        """User display name."""
        return self.full_name or self.username or self.email

    def to_dict(self, include_password: bool = False) -> dict:
        """
        Convert user to dictionary.
        
        Args:
            include_password: Whether to include hashed password in output
            
        Returns:
            dict: User data as dictionary
        """
        data = {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_password:
            data["hashed_password"] = self.hashed_password
        
        return data

    def update_last_login(self) -> None:
        """Update last login timestamp to current time."""
        self.last_login = datetime.now(timezone.utc)

    def is_admin(self) -> bool:
        """Check if user is admin (superuser)."""
        return self.is_superuser

    def can_manage_project(self, project: "Project") -> bool:
        """
        Check if user can manage a project.
        
        Args:
            project: Project to check
            
        Returns:
            bool: True if user owns the project or is superuser
        """
        return self.is_superuser or self.id == project.owner_id

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """
        Create User instance from dictionary.
        
        Args:
            data: Dictionary with user data
            
        Returns:
            User: New User instance
        """
        return cls(
            email=data.get("email"),
            username=data.get("username"),
            hashed_password=data.get("hashed_password"),
            full_name=data.get("full_name"),
            bio=data.get("bio"),
            avatar_url=data.get("avatar_url"),
            is_active=data.get("is_active", True),
            is_superuser=data.get("is_superuser", False),
        )
