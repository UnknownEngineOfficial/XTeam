"""
WebSocket Message Handler Module

This module handles incoming WebSocket messages and routes them to appropriate
handlers. It processes commands like starting agents, cancelling executions,
and managing project operations.

Features:
- Message type routing and validation
- Payload validation and transformation
- Integration with agent manager and task queue
- Error handling and response generation
- Logging and monitoring
- Rate limiting support
"""

import logging
from typing import Any, Callable, Dict, Optional
from enum import Enum
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User
from app.models.project import Project
from app.models.execution import Execution, ExecutionStatus, ExecutionType
from app.services.project_service import ProjectService, get_project_service
from app.services.agent_service import AgentService, get_agent_service
from app.metagpt_integration.agent_manager import AgentManager
from app.metagpt_integration.task_queue import (
    TaskQueue,
    JobPriority,
    get_task_queue,
)
from app.metagpt_integration.streaming import (
    StreamingHandler,
    EventType,
    get_streaming_handler,
)


logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""
    # Agent control
    START_AGENT = "start_agent"
    CANCEL_EXECUTION = "cancel_execution"
    PAUSE_EXECUTION = "pause_execution"
    RESUME_EXECUTION = "resume_execution"
    
    # Project operations
    GET_PROJECT = "get_project"
    UPDATE_PROJECT = "update_project"
    GET_PROJECT_STATUS = "get_project_status"
    
    # Execution operations
    GET_EXECUTION = "get_execution"
    GET_EXECUTION_LOGS = "get_execution_logs"
    
    # File operations
    GET_FILE = "get_file"
    LIST_FILES = "list_files"
    
    # Configuration
    GET_AGENT_CONFIG = "get_agent_config"
    UPDATE_AGENT_CONFIG = "update_agent_config"
    
    # Subscription
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    
    # System
    PING = "ping"
    HEARTBEAT = "heartbeat"


class MessageResponse:
    """
    Represents a WebSocket message response.
    
    Attributes:
        success: Whether the operation was successful
        message_type: Type of response
        data: Response data
        error: Error message if failed
        timestamp: Response timestamp
    """

    def __init__(
        self,
        success: bool,
        message_type: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """Initialize message response."""
        self.success = success
        self.message_type = message_type
        self.data = data or {}
        self.error = error
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "success": self.success,
            "message_type": self.message_type,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class MessageHandler:
    """
    Handles incoming WebSocket messages and routes them to appropriate handlers.
    
    Manages message validation, routing, and response generation.
    """

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
    ):
        """
        Initialize message handler.
        
        Args:
            db: Database session
            settings: Application settings
        """
        self.db = db
        self.settings = settings
        self.project_service = get_project_service(db)
        self.agent_service = get_agent_service(db)
        
        # Message handlers registry
        self.handlers: Dict[MessageType, Callable] = {
            MessageType.START_AGENT: self._handle_start_agent,
            MessageType.CANCEL_EXECUTION: self._handle_cancel_execution,
            MessageType.PAUSE_EXECUTION: self._handle_pause_execution,
            MessageType.RESUME_EXECUTION: self._handle_resume_execution,
            MessageType.GET_PROJECT: self._handle_get_project,
            MessageType.UPDATE_PROJECT: self._handle_update_project,
            MessageType.GET_PROJECT_STATUS: self._handle_get_project_status,
            MessageType.GET_EXECUTION: self._handle_get_execution,
            MessageType.GET_EXECUTION_LOGS: self._handle_get_execution_logs,
            MessageType.GET_FILE: self._handle_get_file,
            MessageType.LIST_FILES: self._handle_list_files,
            MessageType.GET_AGENT_CONFIG: self._handle_get_agent_config,
            MessageType.UPDATE_AGENT_CONFIG: self._handle_update_agent_config,
            MessageType.SUBSCRIBE: self._handle_subscribe,
            MessageType.UNSUBSCRIBE: self._handle_unsubscribe,
            MessageType.PING: self._handle_ping,
            MessageType.HEARTBEAT: self._handle_heartbeat,
        }

    async def handle(
        self,
        message_type: str,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle incoming WebSocket message.
        
        Args:
            message_type: Type of message
            payload: Message payload
            user: User sending the message
            
        Returns:
            MessageResponse object
        """
        try:
            # Validate message type
            try:
                msg_type = MessageType(message_type)
            except ValueError:
                return MessageResponse(
                    success=False,
                    message_type=message_type,
                    error=f"Unknown message type: {message_type}",
                )

            # Get handler
            handler = self.handlers.get(msg_type)
            if not handler:
                return MessageResponse(
                    success=False,
                    message_type=message_type,
                    error=f"No handler for message type: {message_type}",
                )

            # Call handler
            logger.debug(f"Handling message {message_type} for user {user.id}")
            response = await handler(payload, user)
            return response

        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}")
            return MessageResponse(
                success=False,
                message_type=message_type,
                error=f"Internal error: {str(e)}",
            )

    # ========================================================================
    # Agent Control Handlers
    # ========================================================================

    async def _handle_start_agent(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle start agent message.
        
        Payload:
            - project_id: Project ID
            - execution_type: Type of execution (full, partial, test)
            - requirements: Optional requirements
        """
        try:
            project_id = payload.get("project_id")
            if not project_id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.START_AGENT.value,
                    error="Missing project_id",
                )

            # Get project
            project = await self.project_service.get_project(project_id, user.id)
            if not project:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.START_AGENT.value,
                    error="Project not found",
                )

            # Get execution type
            execution_type_str = payload.get("execution_type", "full")
            try:
                execution_type = ExecutionType(execution_type_str)
            except ValueError:
                execution_type = ExecutionType.FULL

            # Create execution
            execution = Execution(
                project_id=project.id,
                user_id=user.id,
                execution_type=execution_type,
                status=ExecutionStatus.PENDING,
            )
            self.db.add(execution)
            await self.db.flush()

            # Enqueue job
            task_queue = await get_task_queue(self.settings)
            job_id = await task_queue.enqueue_job(
                job_type="workflow",
                payload={
                    "project_id": str(project.id),
                    "execution_id": str(execution.id),
                    "user_id": str(user.id),
                    "execution_type": execution_type.value,
                    "requirements": payload.get("requirements"),
                },
                priority=JobPriority.HIGH,
                max_retries=2,
                timeout_seconds=3600,
                tags=["workflow", str(project.id)],
            )

            await self.db.commit()

            # Emit event
            streaming = await get_streaming_handler()
            await streaming.emit_status(
                status="started",
                details={"execution_id": str(execution.id), "job_id": job_id},
                source="message_handler",
                execution_id=str(execution.id),
                project_id=str(project.id),
            )

            logger.info(f"Started agent for project {project.id}, execution {execution.id}")

            return MessageResponse(
                success=True,
                message_type=MessageType.START_AGENT.value,
                data={
                    "execution_id": str(execution.id),
                    "job_id": job_id,
                    "status": execution.status.value,
                },
            )

        except Exception as e:
            logger.error(f"Error starting agent: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.START_AGENT.value,
                error=str(e),
            )

    async def _handle_cancel_execution(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle cancel execution message.
        
        Payload:
            - execution_id: Execution ID to cancel
        """
        try:
            execution_id = payload.get("execution_id")
            if not execution_id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.CANCEL_EXECUTION.value,
                    error="Missing execution_id",
                )

            # Get execution
            execution = await self.db.get(Execution, UUID(execution_id))
            if not execution or execution.user_id != user.id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.CANCEL_EXECUTION.value,
                    error="Execution not found",
                )

            # Cancel execution
            execution.status = ExecutionStatus.CANCELLED
            await self.db.commit()

            # Emit event
            streaming = await get_streaming_handler()
            await streaming.emit_status(
                status="cancelled",
                source="message_handler",
                execution_id=str(execution.id),
                project_id=str(execution.project_id),
            )

            logger.info(f"Cancelled execution {execution.id}")

            return MessageResponse(
                success=True,
                message_type=MessageType.CANCEL_EXECUTION.value,
                data={"execution_id": str(execution.id), "status": execution.status.value},
            )

        except Exception as e:
            logger.error(f"Error cancelling execution: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.CANCEL_EXECUTION.value,
                error=str(e),
            )

    async def _handle_pause_execution(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """Handle pause execution message."""
        # Placeholder for pause functionality
        return MessageResponse(
            success=False,
            message_type=MessageType.PAUSE_EXECUTION.value,
            error="Pause execution not yet implemented",
        )

    async def _handle_resume_execution(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """Handle resume execution message."""
        # Placeholder for resume functionality
        return MessageResponse(
            success=False,
            message_type=MessageType.RESUME_EXECUTION.value,
            error="Resume execution not yet implemented",
        )

    # ========================================================================
    # Project Handlers
    # ========================================================================

    async def _handle_get_project(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle get project message.
        
        Payload:
            - project_id: Project ID
        """
        try:
            project_id = payload.get("project_id")
            if not project_id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_PROJECT.value,
                    error="Missing project_id",
                )

            project = await self.project_service.get_project(project_id, user.id)
            if not project:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_PROJECT.value,
                    error="Project not found",
                )

            return MessageResponse(
                success=True,
                message_type=MessageType.GET_PROJECT.value,
                data={
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "status": project.status.value,
                    "progress": project.progress,
                },
            )

        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.GET_PROJECT.value,
                error=str(e),
            )

    async def _handle_update_project(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle update project message.
        
        Payload:
            - project_id: Project ID
            - name: Optional project name
            - description: Optional project description
        """
        try:
            project_id = payload.get("project_id")
            if not project_id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.UPDATE_PROJECT.value,
                    error="Missing project_id",
                )

            project = await self.project_service.get_project(project_id, user.id)
            if not project:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.UPDATE_PROJECT.value,
                    error="Project not found",
                )

            # Update fields
            if "name" in payload:
                project.name = payload["name"]
            if "description" in payload:
                project.description = payload["description"]

            await self.db.commit()

            return MessageResponse(
                success=True,
                message_type=MessageType.UPDATE_PROJECT.value,
                data={"project_id": str(project.id)},
            )

        except Exception as e:
            logger.error(f"Error updating project: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.UPDATE_PROJECT.value,
                error=str(e),
            )

    async def _handle_get_project_status(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle get project status message.
        
        Payload:
            - project_id: Project ID
        """
        try:
            project_id = payload.get("project_id")
            if not project_id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_PROJECT_STATUS.value,
                    error="Missing project_id",
                )

            project = await self.project_service.get_project(project_id, user.id)
            if not project:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_PROJECT_STATUS.value,
                    error="Project not found",
                )

            return MessageResponse(
                success=True,
                message_type=MessageType.GET_PROJECT_STATUS.value,
                data={
                    "project_id": str(project.id),
                    "status": project.status.value,
                    "progress": project.progress,
                },
            )

        except Exception as e:
            logger.error(f"Error getting project status: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.GET_PROJECT_STATUS.value,
                error=str(e),
            )

    # ========================================================================
    # Execution Handlers
    # ========================================================================

    async def _handle_get_execution(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle get execution message.
        
        Payload:
            - execution_id: Execution ID
        """
        try:
            execution_id = payload.get("execution_id")
            if not execution_id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_EXECUTION.value,
                    error="Missing execution_id",
                )

            execution = await self.db.get(Execution, UUID(execution_id))
            if not execution or execution.user_id != user.id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_EXECUTION.value,
                    error="Execution not found",
                )

            return MessageResponse(
                success=True,
                message_type=MessageType.GET_EXECUTION.value,
                data={
                    "execution_id": str(execution.id),
                    "status": execution.status.value,
                    "execution_type": execution.execution_type.value,
                    "created_at": execution.created_at.isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Error getting execution: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.GET_EXECUTION.value,
                error=str(e),
            )

    async def _handle_get_execution_logs(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle get execution logs message.
        
        Payload:
            - execution_id: Execution ID
            - limit: Optional limit on number of logs
        """
        try:
            execution_id = payload.get("execution_id")
            if not execution_id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_EXECUTION_LOGS.value,
                    error="Missing execution_id",
                )

            execution = await self.db.get(Execution, UUID(execution_id))
            if not execution or execution.user_id != user.id:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_EXECUTION_LOGS.value,
                    error="Execution not found",
                )

            logs = execution.agent_logs or []
            limit = payload.get("limit", 100)
            logs = logs[-limit:]

            return MessageResponse(
                success=True,
                message_type=MessageType.GET_EXECUTION_LOGS.value,
                data={"execution_id": str(execution.id), "logs": logs},
            )

        except Exception as e:
            logger.error(f"Error getting execution logs: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.GET_EXECUTION_LOGS.value,
                error=str(e),
            )

    # ========================================================================
    # File Handlers
    # ========================================================================

    async def _handle_get_file(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """Handle get file message (placeholder)."""
        return MessageResponse(
            success=False,
            message_type=MessageType.GET_FILE.value,
            error="Get file not yet implemented",
        )

    async def _handle_list_files(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """Handle list files message (placeholder)."""
        return MessageResponse(
            success=False,
            message_type=MessageType.LIST_FILES.value,
            error="List files not yet implemented",
        )

    # ========================================================================
    # Configuration Handlers
    # ========================================================================

    async def _handle_get_agent_config(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle get agent config message.
        
        Payload:
            - agent_role: Agent role
        """
        try:
            agent_role = payload.get("agent_role")
            if not agent_role:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_AGENT_CONFIG.value,
                    error="Missing agent_role",
                )

            config = await self.agent_service.get_agent_config_for_role(
                user.id,
                agent_role,
            )

            if not config:
                return MessageResponse(
                    success=False,
                    message_type=MessageType.GET_AGENT_CONFIG.value,
                    error="Agent config not found",
                )

            return MessageResponse(
                success=True,
                message_type=MessageType.GET_AGENT_CONFIG.value,
                data={
                    "agent_role": config.agent_role.value,
                    "llm_provider": config.llm_provider.value,
                    "llm_model": config.llm_model,
                },
            )

        except Exception as e:
            logger.error(f"Error getting agent config: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.GET_AGENT_CONFIG.value,
                error=str(e),
            )

    async def _handle_update_agent_config(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """Handle update agent config message (placeholder)."""
        return MessageResponse(
            success=False,
            message_type=MessageType.UPDATE_AGENT_CONFIG.value,
            error="Update agent config not yet implemented",
        )

    # ========================================================================
    # Subscription Handlers
    # ========================================================================

    async def _handle_subscribe(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """
        Handle subscribe message.
        
        Payload:
            - execution_id: Optional execution ID to subscribe to
            - project_id: Optional project ID to subscribe to
        """
        try:
            execution_id = payload.get("execution_id")
            project_id = payload.get("project_id")

            return MessageResponse(
                success=True,
                message_type=MessageType.SUBSCRIBE.value,
                data={
                    "execution_id": execution_id,
                    "project_id": project_id,
                },
            )

        except Exception as e:
            logger.error(f"Error subscribing: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.SUBSCRIBE.value,
                error=str(e),
            )

    async def _handle_unsubscribe(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """Handle unsubscribe message."""
        try:
            execution_id = payload.get("execution_id")
            project_id = payload.get("project_id")

            return MessageResponse(
                success=True,
                message_type=MessageType.UNSUBSCRIBE.value,
                data={
                    "execution_id": execution_id,
                    "project_id": project_id,
                },
            )

        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
            return MessageResponse(
                success=False,
                message_type=MessageType.UNSUBSCRIBE.value,
                error=str(e),
            )

    # ========================================================================
    # System Handlers
    # ========================================================================

    async def _handle_ping(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """Handle ping message."""
        return MessageResponse(
            success=True,
            message_type=MessageType.PING.value,
            data={"pong": True},
        )

    async def _handle_heartbeat(
        self,
        payload: Dict[str, Any],
        user: User,
    ) -> MessageResponse:
        """Handle heartbeat message."""
        return MessageResponse(
            success=True,
            message_type=MessageType.HEARTBEAT.value,
            data={"timestamp": datetime.utcnow().isoformat()},
        )


def get_message_handler(db: AsyncSession, settings: Settings) -> MessageHandler:
    """
    Get message handler instance.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        MessageHandler instance
    """
    return MessageHandler(db, settings)
