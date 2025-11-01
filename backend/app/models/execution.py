"""
Execution Model

This module defines the Execution ORM model for tracking project executions.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Index, ForeignKey, Enum, Float, Integer
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ExecutionStatus(str, enum.Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionType(str, enum.Enum):
    """Execution type enumeration."""
    FULL = "full"  # Full project execution
    PARTIAL = "partial"  # Partial/incremental execution
    TEST = "test"  # Test execution
    DEPLOYMENT = "deployment"  # Deployment execution


class Execution(Base):
    """
    Execution model representing project execution runs.
    
    Attributes:
        id: Unique execution identifier (UUID)
        project_id: Project ID (FK to Project)
        user_id: User ID who triggered execution (FK to User)
        execution_type: Type of execution (full, partial, test, deployment)
        status: Execution status (pending, running, paused, completed, failed, cancelled, timeout)
        agent_logs: Detailed logs from agent execution (JSON)
        output: Execution output/results (JSON)
        error_message: Error message if execution failed
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp
        duration_seconds: Total execution duration in seconds
        retry_count: Number of retries
        max_retries: Maximum allowed retries
        metadata: Additional execution metadata (JSON)
    """

    __tablename__ = "executions"
    
    # Class constants for execution states
    CANCELLABLE_STATUSES = {ExecutionStatus.PENDING, ExecutionStatus.RUNNING, ExecutionStatus.PAUSED}
    PAUSABLE_STATUSES = {ExecutionStatus.RUNNING, ExecutionStatus.PENDING}
    RESUMABLE_STATUSES = {ExecutionStatus.PAUSED}
    ACTIVE_STATUSES = {ExecutionStatus.RUNNING, ExecutionStatus.PAUSED}
    FINISHED_STATUSES = {ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT}

    # ========================================================================
    # Primary Key
    # ========================================================================

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        doc="Unique execution identifier"
    )

    # ========================================================================
    # Foreign Keys
    # ========================================================================

    project_id = Column(
        String,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project ID"
    )

    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User ID who triggered execution"
    )

    # ========================================================================
    # Execution Configuration
    # ========================================================================

    execution_type = Column(
        Enum(ExecutionType),
        default=ExecutionType.FULL,
        nullable=False,
        doc="Type of execution"
    )

    status = Column(
        Enum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
        nullable=False,
        index=True,
        doc="Execution status"
    )

    # ========================================================================
    # Execution Logs and Output
    # ========================================================================

    agent_logs = Column(
        Text,
        default="[]",
        nullable=False,
        doc="Detailed logs from agent execution"
    )

    output = Column(
        Text,
        default="{}",
        nullable=False,
        doc="Execution output/results"
    )

    error_message = Column(
        Text,
        nullable=True,
        doc="Error message if execution failed"
    )

    # ========================================================================
    # Timestamp Fields
    # ========================================================================

    started_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Execution start timestamp"
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Execution completion timestamp"
    )

    duration_seconds = Column(
        Float,
        nullable=True,
        doc="Total execution duration in seconds"
    )

    # ========================================================================
    # Retry Configuration
    # ========================================================================

    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of retries"
    )

    max_retries = Column(
        Integer,
        default=3,
        nullable=False,
        doc="Maximum allowed retries"
    )

    # ========================================================================
    # Metadata
    # ========================================================================

    execution_metadata = Column(
        Text,
        default="{}",
        nullable=False,
        doc="Additional execution metadata"
    )

    # ========================================================================
    # Relationships
    # ========================================================================

    # Relationship to project (many executions belong to one project)
    project = relationship(
        "Project",
        back_populates="executions",
        foreign_keys=[project_id],
        doc="Associated project"
    )

    # Relationship to user (many executions belong to one user)
    user = relationship(
        "User",
        back_populates="executions",
        foreign_keys=[user_id],
        doc="User who triggered execution"
    )

    # ========================================================================
    # Indexes
    # ========================================================================

    __table_args__ = (
        Index("idx_execution_project_id", "project_id"),
        Index("idx_execution_user_id", "user_id"),
        Index("idx_execution_status", "status"),
        Index("idx_execution_started_at", "started_at"),
        Index("idx_execution_project_status", "project_id", "status"),
        Index("idx_execution_project_started", "project_id", "started_at"),
    )

    # ========================================================================
    # Methods
    # ========================================================================

    def __repr__(self) -> str:
        """String representation of Execution."""
        return f"<Execution(id={self.id}, project_id={self.project_id}, status={self.status})>"

    def __str__(self) -> str:
        """Execution display name."""
        return f"Execution {self.id} ({self.status.value})"

    def to_dict(self, include_logs: bool = True, include_output: bool = True) -> dict:
        """
        Convert execution to dictionary.
        
        Args:
            include_logs: Whether to include agent logs
            include_output: Whether to include execution output
            
        Returns:
            dict: Execution data as dictionary
        """
        data = {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "execution_type": self.execution_type.value if self.execution_type else None,
            "status": self.status.value if self.status else None,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.execution_metadata,
        }
        
        if include_logs:
            data["agent_logs"] = self.agent_logs
        
        if include_output:
            data["output"] = self.output
        
        return data

    def start(self) -> None:
        """Mark execution as started."""
        if self.status == ExecutionStatus.PENDING:
            self.status = ExecutionStatus.RUNNING
            self.started_at = datetime.now(timezone.utc)

    def complete(self, output: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark execution as completed.
        
        Args:
            output: Optional execution output
        """
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self._calculate_duration()
        
        if output:
            self.output = output

    def fail(self, error_message: str, output: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark execution as failed.
        
        Args:
            error_message: Error message
            output: Optional partial output
        """
        self.status = ExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)
        self._calculate_duration()
        
        if output:
            self.output = output

    def pause(self) -> None:
        """Pause execution."""
        if self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.PAUSED

    def resume(self) -> None:
        """Resume execution."""
        if self.status == ExecutionStatus.PAUSED:
            self.status = ExecutionStatus.RUNNING

    def cancel(self) -> None:
        """Cancel execution."""
        if self.status in self.CANCELLABLE_STATUSES:
            self.status = ExecutionStatus.CANCELLED
            self.completed_at = datetime.now(timezone.utc)
            self._calculate_duration()

    def timeout(self) -> None:
        """Mark execution as timed out."""
        self.status = ExecutionStatus.TIMEOUT
        self.completed_at = datetime.now(timezone.utc)
        self._calculate_duration()
        self.error_message = "Execution timed out"

    def can_retry(self) -> bool:
        """
        Check if execution can be retried.
        
        Returns:
            bool: True if retry count is less than max retries
        """
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1

    def add_log(self, agent: str, message: str, level: str = "info", timestamp: Optional[datetime] = None) -> None:
        """
        Add a log entry to agent logs.
        
        Args:
            agent: Agent name
            message: Log message
            level: Log level (info, warning, error, debug)
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.agent_logs:
            self.agent_logs = []
        
        log_entry = {
            "agent": agent,
            "message": message,
            "level": level,
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
        }
        
        self.agent_logs.append(log_entry)

    def add_logs(self, logs: List[Dict[str, Any]]) -> None:
        """
        Add multiple log entries.
        
        Args:
            logs: List of log entries
        """
        if not self.agent_logs:
            self.agent_logs = []
        
        for log in logs:
            if "timestamp" not in log:
                log["timestamp"] = datetime.now(timezone.utc).isoformat()
            self.agent_logs.append(log)

    def get_logs(self, agent: Optional[str] = None, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get filtered logs.
        
        Args:
            agent: Optional agent name filter
            level: Optional log level filter
            
        Returns:
            List of matching log entries
        """
        if not self.agent_logs:
            return []
        
        logs = self.agent_logs
        
        if agent:
            logs = [log for log in logs if log.get("agent") == agent]
        
        if level:
            logs = [log for log in logs if log.get("level") == level]
        
        return logs

    def is_running(self) -> bool:
        """Check if execution is currently running or active."""
        return self.status in self.ACTIVE_STATUSES

    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return self.status == ExecutionStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == ExecutionStatus.FAILED

    def is_cancelled(self) -> bool:
        """Check if execution was cancelled."""
        return self.status == ExecutionStatus.CANCELLED

    def is_finished(self) -> bool:
        """Check if execution is finished (completed, failed, cancelled, or timeout)."""
        return self.status in self.FINISHED_STATUSES

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata key-value pair.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        if not self.execution_metadata:
            self.execution_metadata = {}
        self.execution_metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value by key.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        if not self.execution_metadata:
            return default
        return self.execution_metadata.get(key, default)

    def _calculate_duration(self) -> None:
        """Calculate and update execution duration."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = delta.total_seconds()

    @classmethod
    def from_dict(cls, data: dict, project_id: str, user_id: Optional[str] = None) -> "Execution":
        """
        Create Execution instance from dictionary.
        
        Args:
            data: Dictionary with execution data
            project_id: Project ID
            user_id: Optional user ID
            
        Returns:
            Execution: New Execution instance
        """
        return cls(
            project_id=project_id,
            user_id=user_id,
            execution_type=ExecutionType(data.get("execution_type", "full")),
            status=ExecutionStatus(data.get("status", "pending")),
            agent_logs=data.get("agent_logs", []),
            output=data.get("output", {}),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )
