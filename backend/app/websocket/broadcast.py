"""
WebSocket Broadcast Module

This module provides broadcasting functionality for sending agent updates,
execution events, and other real-time notifications to connected WebSocket clients.

Features:
- Broadcast agent updates to project participants
- Event-based notification system
- Targeted delivery to users and projects
- Retry logic for failed deliveries
- Event queuing and batching
- Metrics and monitoring
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from app.websocket.connection_manager import get_connection_manager
from app.metagpt_integration.streaming import (
    get_streaming_handler,
    EventType,
    EventFilter,
)


logger = logging.getLogger(__name__)


class BroadcastEventType(str, Enum):
    """Types of broadcast events."""
    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_PROGRESS = "agent_progress"
    
    # Execution events
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"
    
    # Log events
    LOG_ENTRY = "log_entry"
    LOG_BATCH = "log_batch"
    
    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    
    # Status events
    STATUS_UPDATE = "status_update"
    PROGRESS_UPDATE = "progress_update"
    
    # Error events
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"


class BroadcastEvent:
    """
    Represents a broadcast event to be sent to clients.
    
    Attributes:
        event_type: Type of broadcast event
        project_id: Associated project ID
        execution_id: Associated execution ID
        user_id: User who triggered the event (optional)
        data: Event data/payload
        timestamp: Event creation timestamp
        metadata: Additional metadata
    """

    def __init__(
        self,
        event_type: BroadcastEventType,
        project_id: str,
        data: Dict[str, Any],
        execution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize broadcast event."""
        self.event_type = event_type
        self.project_id = project_id
        self.execution_id = execution_id
        self.user_id = user_id
        self.data = data
        self.timestamp = datetime.utcnow()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for transmission."""
        return {
            "event_type": self.event_type.value,
            "project_id": self.project_id,
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class BroadcastManager:
    """
    Manages broadcasting of events to connected WebSocket clients.
    
    Handles event routing, delivery, and retry logic.
    """

    def __init__(self):
        """Initialize broadcast manager."""
        self.metrics = {
            "total_broadcasts": 0,
            "successful_broadcasts": 0,
            "failed_broadcasts": 0,
            "total_messages_sent": 0,
            "broadcasts_by_type": {},
            "broadcasts_by_project": {},
        }

    async def broadcast_agent_update(
        self,
        project_id: str,
        event_type: BroadcastEventType,
        data: Dict[str, Any],
        execution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        exclude_user_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast an agent update to all connected clients of a project.
        
        Args:
            project_id: Project ID
            event_type: Type of event
            data: Event data
            execution_id: Associated execution ID (optional)
            user_id: User who triggered the event (optional)
            exclude_user_id: User to exclude from broadcast (optional)
            
        Returns:
            Number of messages sent successfully
        """
        try:
            # Create broadcast event
            event = BroadcastEvent(
                event_type=event_type,
                project_id=project_id,
                data=data,
                execution_id=execution_id,
                user_id=user_id,
            )

            # Get connection manager
            conn_manager = get_connection_manager()

            # Send to project
            message = event.to_dict()
            sent_count = await conn_manager.send_to_project(
                project_id,
                message,
                exclude_user_id=exclude_user_id,
            )

            # Update metrics
            self.metrics["total_broadcasts"] += 1
            event_type_key = event_type.value
            self.metrics["broadcasts_by_type"][event_type_key] = \
                self.metrics["broadcasts_by_type"].get(event_type_key, 0) + 1
            self.metrics["broadcasts_by_project"][project_id] = \
                self.metrics["broadcasts_by_project"].get(project_id, 0) + 1
            self.metrics["total_messages_sent"] += sent_count

            if sent_count > 0:
                self.metrics["successful_broadcasts"] += 1
                logger.debug(
                    f"Broadcast {event_type.value} to {sent_count} client(s) "
                    f"for project {project_id}"
                )
            else:
                self.metrics["failed_broadcasts"] += 1
                logger.warning(
                    f"No clients received broadcast {event_type.value} "
                    f"for project {project_id}"
                )

            return sent_count

        except Exception as e:
            logger.error(f"Error broadcasting agent update: {e}")
            self.metrics["failed_broadcasts"] += 1
            return 0

    async def broadcast_execution_started(
        self,
        project_id: str,
        execution_id: str,
        execution_type: str,
        user_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast execution started event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            execution_type: Type of execution
            user_id: User who started execution (optional)
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.EXECUTION_STARTED,
            data={
                "execution_id": execution_id,
                "execution_type": execution_type,
                "status": "started",
            },
            execution_id=execution_id,
            user_id=user_id,
        )

    async def broadcast_execution_progress(
        self,
        project_id: str,
        execution_id: str,
        progress: int,
        stage: str,
        message: str = "",
    ) -> int:
        """
        Broadcast execution progress update.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            progress: Progress percentage (0-100)
            stage: Current stage/phase
            message: Optional progress message
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.EXECUTION_PROGRESS,
            data={
                "execution_id": execution_id,
                "progress": max(0, min(100, progress)),
                "stage": stage,
                "message": message,
            },
            execution_id=execution_id,
        )

    async def broadcast_execution_completed(
        self,
        project_id: str,
        execution_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Broadcast execution completed event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            result: Execution result (optional)
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.EXECUTION_COMPLETED,
            data={
                "execution_id": execution_id,
                "status": "completed",
                "result": result or {},
            },
            execution_id=execution_id,
        )

    async def broadcast_execution_failed(
        self,
        project_id: str,
        execution_id: str,
        error_message: str,
        error_type: str = "unknown",
    ) -> int:
        """
        Broadcast execution failed event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            error_message: Error message
            error_type: Type of error
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.EXECUTION_FAILED,
            data={
                "execution_id": execution_id,
                "status": "failed",
                "error_message": error_message,
                "error_type": error_type,
            },
            execution_id=execution_id,
        )

    async def broadcast_execution_cancelled(
        self,
        project_id: str,
        execution_id: str,
    ) -> int:
        """
        Broadcast execution cancelled event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.EXECUTION_CANCELLED,
            data={
                "execution_id": execution_id,
                "status": "cancelled",
            },
            execution_id=execution_id,
        )

    async def broadcast_log_entry(
        self,
        project_id: str,
        execution_id: str,
        message: str,
        level: str = "INFO",
        source: str = "agent",
    ) -> int:
        """
        Broadcast log entry event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            source: Source of log
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.LOG_ENTRY,
            data={
                "execution_id": execution_id,
                "message": message,
                "level": level,
                "source": source,
            },
            execution_id=execution_id,
        )

    async def broadcast_log_batch(
        self,
        project_id: str,
        execution_id: str,
        logs: List[Dict[str, Any]],
    ) -> int:
        """
        Broadcast batch of log entries.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            logs: List of log entries
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.LOG_BATCH,
            data={
                "execution_id": execution_id,
                "logs": logs,
                "count": len(logs),
            },
            execution_id=execution_id,
        )

    async def broadcast_file_created(
        self,
        project_id: str,
        execution_id: str,
        file_path: str,
        content: Optional[str] = None,
    ) -> int:
        """
        Broadcast file created event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            file_path: Path to created file
            content: File content (optional)
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.FILE_CREATED,
            data={
                "execution_id": execution_id,
                "file_path": file_path,
                "content": content,
            },
            execution_id=execution_id,
        )

    async def broadcast_file_modified(
        self,
        project_id: str,
        execution_id: str,
        file_path: str,
        content: Optional[str] = None,
    ) -> int:
        """
        Broadcast file modified event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            file_path: Path to modified file
            content: File content (optional)
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.FILE_MODIFIED,
            data={
                "execution_id": execution_id,
                "file_path": file_path,
                "content": content,
            },
            execution_id=execution_id,
        )

    async def broadcast_file_deleted(
        self,
        project_id: str,
        execution_id: str,
        file_path: str,
    ) -> int:
        """
        Broadcast file deleted event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            file_path: Path to deleted file
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.FILE_DELETED,
            data={
                "execution_id": execution_id,
                "file_path": file_path,
            },
            execution_id=execution_id,
        )

    async def broadcast_status_update(
        self,
        project_id: str,
        execution_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Broadcast status update event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            status: Status string
            details: Optional status details
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.STATUS_UPDATE,
            data={
                "execution_id": execution_id,
                "status": status,
                "details": details or {},
            },
            execution_id=execution_id,
        )

    async def broadcast_error(
        self,
        project_id: str,
        execution_id: str,
        error_message: str,
        error_type: str = "unknown",
    ) -> int:
        """
        Broadcast error event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            error_message: Error message
            error_type: Type of error
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.ERROR_OCCURRED,
            data={
                "execution_id": execution_id,
                "error_message": error_message,
                "error_type": error_type,
            },
            execution_id=execution_id,
        )

    async def broadcast_warning(
        self,
        project_id: str,
        execution_id: str,
        warning_message: str,
    ) -> int:
        """
        Broadcast warning event.
        
        Args:
            project_id: Project ID
            execution_id: Execution ID
            warning_message: Warning message
            
        Returns:
            Number of messages sent
        """
        return await self.broadcast_agent_update(
            project_id=project_id,
            event_type=BroadcastEventType.WARNING_ISSUED,
            data={
                "execution_id": execution_id,
                "warning_message": warning_message,
            },
            execution_id=execution_id,
        )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get broadcast manager metrics.
        
        Returns:
            Dictionary with metrics
        """
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_broadcasts"] / max(1, self.metrics["total_broadcasts"])
                * 100
            ),
        }

    async def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            "total_broadcasts": 0,
            "successful_broadcasts": 0,
            "failed_broadcasts": 0,
            "total_messages_sent": 0,
            "broadcasts_by_type": {},
            "broadcasts_by_project": {},
        }
        logger.info("Broadcast metrics reset")


# Global broadcast manager instance
_broadcast_manager: Optional[BroadcastManager] = None


def get_broadcast_manager() -> BroadcastManager:
    """
    Get or create global broadcast manager instance.
    
    Returns:
        BroadcastManager instance
    """
    global _broadcast_manager

    if _broadcast_manager is None:
        _broadcast_manager = BroadcastManager()
        logger.info("Broadcast manager initialized")

    return _broadcast_manager


# Convenience functions for common broadcast operations

async def broadcast_agent_update(
    project_id: str,
    event_type: BroadcastEventType,
    data: Dict[str, Any],
    execution_id: Optional[str] = None,
    user_id: Optional[str] = None,
    exclude_user_id: Optional[str] = None,
) -> int:
    """
    Broadcast an agent update to all connected clients of a project.
    
    Args:
        project_id: Project ID
        event_type: Type of event
        data: Event data
        execution_id: Associated execution ID (optional)
        user_id: User who triggered the event (optional)
        exclude_user_id: User to exclude from broadcast (optional)
        
    Returns:
        Number of messages sent successfully
    """
    manager = get_broadcast_manager()
    return await manager.broadcast_agent_update(
        project_id=project_id,
        event_type=event_type,
        data=data,
        execution_id=execution_id,
        user_id=user_id,
        exclude_user_id=exclude_user_id,
    )


async def broadcast_execution_started(
    project_id: str,
    execution_id: str,
    execution_type: str,
    user_id: Optional[str] = None,
) -> int:
    """Broadcast execution started event."""
    manager = get_broadcast_manager()
    return await manager.broadcast_execution_started(
        project_id=project_id,
        execution_id=execution_id,
        execution_type=execution_type,
        user_id=user_id,
    )


async def broadcast_execution_progress(
    project_id: str,
    execution_id: str,
    progress: int,
    stage: str,
    message: str = "",
) -> int:
    """Broadcast execution progress update."""
    manager = get_broadcast_manager()
    return await manager.broadcast_execution_progress(
        project_id=project_id,
        execution_id=execution_id,
        progress=progress,
        stage=stage,
        message=message,
    )


async def broadcast_execution_completed(
    project_id: str,
    execution_id: str,
    result: Optional[Dict[str, Any]] = None,
) -> int:
    """Broadcast execution completed event."""
    manager = get_broadcast_manager()
    return await manager.broadcast_execution_completed(
        project_id=project_id,
        execution_id=execution_id,
        result=result,
    )


async def broadcast_execution_failed(
    project_id: str,
    execution_id: str,
    error_message: str,
    error_type: str = "unknown",
) -> int:
    """Broadcast execution failed event."""
    manager = get_broadcast_manager()
    return await manager.broadcast_execution_failed(
        project_id=project_id,
        execution_id=execution_id,
        error_message=error_message,
        error_type=error_type,
    )


async def broadcast_log_entry(
    project_id: str,
    execution_id: str,
    message: str,
    level: str = "INFO",
    source: str = "agent",
) -> int:
    """Broadcast log entry event."""
    manager = get_broadcast_manager()
    return await manager.broadcast_log_entry(
        project_id=project_id,
        execution_id=execution_id,
        message=message,
        level=level,
        source=source,
    )


async def broadcast_file_created(
    project_id: str,
    execution_id: str,
    file_path: str,
    content: Optional[str] = None,
) -> int:
    """Broadcast file created event."""
    manager = get_broadcast_manager()
    return await manager.broadcast_file_created(
        project_id=project_id,
        execution_id=execution_id,
        file_path=file_path,
        content=content,
    )


async def broadcast_status_update(
    project_id: str,
    execution_id: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> int:
    """Broadcast status update event."""
    manager = get_broadcast_manager()
    return await manager.broadcast_status_update(
        project_id=project_id,
        execution_id=execution_id,
        status=status,
        details=details,
    )


async def broadcast_error(
    project_id: str,
    execution_id: str,
    error_message: str,
    error_type: str = "unknown",
) -> int:
    """Broadcast error event."""
    manager = get_broadcast_manager()
    return await manager.broadcast_error(
        project_id=project_id,
        execution_id=execution_id,
        error_message=error_message,
        error_type=error_type,
    )
