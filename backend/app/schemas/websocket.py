"""
WebSocket Schemas

This module defines Pydantic models for WebSocket message types and communication.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# Message Type Enums
# ============================================================================

class MessageType(str, Enum):
    """WebSocket message type enumeration."""
    AGENT_MESSAGE = "agent_message"
    STATUS_UPDATE = "status_update"
    FILE_UPDATE = "file_update"
    ERROR_MESSAGE = "error_message"
    LOG_MESSAGE = "log_message"
    PROGRESS_UPDATE = "progress_update"
    EXECUTION_START = "execution_start"
    EXECUTION_COMPLETE = "execution_complete"
    CONNECTION_ACK = "connection_ack"
    HEARTBEAT = "heartbeat"
    COMMAND = "command"


class AgentRole(str, Enum):
    """Agent role enumeration."""
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    QA_ENGINEER = "qa_engineer"
    PROJECT_MANAGER = "project_manager"


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class FileOperation(str, Enum):
    """File operation type enumeration."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RENAME = "rename"


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Base Message Schema
# ============================================================================

class BaseMessage(BaseModel):
    """
    Base schema for all WebSocket messages.
    
    Attributes:
        type: Message type
        timestamp: Message timestamp
        project_id: Associated project ID
        execution_id: Associated execution ID
    """
    type: MessageType = Field(..., description="Message type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    project_id: str = Field(..., description="Associated project ID")
    execution_id: Optional[str] = Field(None, description="Associated execution ID")

    class Config:
        """Pydantic configuration."""
        use_enum_values = False


# ============================================================================
# Agent Message Schema
# ============================================================================

class AgentMessage(BaseMessage):
    """
    Schema for agent communication messages.
    
    Attributes:
        type: Message type (agent_message)
        agent_role: Role of the agent sending the message
        agent_name: Name of the agent
        content: Message content
        metadata: Additional metadata
    """
    type: Literal[MessageType.AGENT_MESSAGE] = MessageType.AGENT_MESSAGE
    agent_role: AgentRole = Field(..., description="Role of the agent")
    agent_name: str = Field(..., description="Name of the agent")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

    @validator("content")
    def validate_content(cls, v):
        """Validate message content is not empty."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "agent_message",
                "timestamp": "2024-01-20T15:45:00Z",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "agent_role": "architect",
                "agent_name": "Architect Agent",
                "content": "I have analyzed the requirements and created the system architecture.",
                "metadata": {"step": 1, "total_steps": 5}
            }
        }


# ============================================================================
# Status Update Schema
# ============================================================================

class StatusUpdate(BaseMessage):
    """
    Schema for execution status update messages.
    
    Attributes:
        type: Message type (status_update)
        status: Current execution status
        message: Status message
        details: Additional status details
    """
    type: Literal[MessageType.STATUS_UPDATE] = MessageType.STATUS_UPDATE
    status: ExecutionStatus = Field(..., description="Current execution status")
    message: str = Field(..., description="Status message")
    details: Dict[str, Any] = Field(default={}, description="Additional status details")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "status_update",
                "timestamp": "2024-01-20T15:45:00Z",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "running",
                "message": "Execution is in progress",
                "details": {"current_step": "code_generation", "agents_active": 2}
            }
        }


# ============================================================================
# File Update Schema
# ============================================================================

class FileUpdate(BaseMessage):
    """
    Schema for file operation messages.
    
    Attributes:
        type: Message type (file_update)
        operation: Type of file operation
        file_path: Path to the file
        file_content: File content (for create/update operations)
        old_path: Old file path (for rename operations)
        language: Programming language of the file
    """
    type: Literal[MessageType.FILE_UPDATE] = MessageType.FILE_UPDATE
    operation: FileOperation = Field(..., description="Type of file operation")
    file_path: str = Field(..., description="Path to the file")
    file_content: Optional[str] = Field(None, description="File content")
    old_path: Optional[str] = Field(None, description="Old file path (for rename)")
    language: Optional[str] = Field(None, description="Programming language")

    @validator("file_path")
    def validate_file_path(cls, v):
        """Validate file path is not empty."""
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "file_update",
                "timestamp": "2024-01-20T15:45:00Z",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "operation": "create",
                "file_path": "src/main.py",
                "file_content": "def main():\n    print('Hello, World!')",
                "language": "python"
            }
        }


# ============================================================================
# Error Message Schema
# ============================================================================

class ErrorMessage(BaseMessage):
    """
    Schema for error messages.
    
    Attributes:
        type: Message type (error_message)
        error_code: Error code
        error_message: Error message
        error_details: Detailed error information
        stack_trace: Optional stack trace
        recoverable: Whether the error is recoverable
    """
    type: Literal[MessageType.ERROR_MESSAGE] = MessageType.ERROR_MESSAGE
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_details: Optional[str] = Field(None, description="Detailed error information")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    recoverable: bool = Field(default=False, description="Whether error is recoverable")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "error_message",
                "timestamp": "2024-01-20T15:45:00Z",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "error_code": "AGENT_TIMEOUT",
                "error_message": "Agent execution timed out",
                "error_details": "Agent did not respond within 300 seconds",
                "recoverable": True
            }
        }


# ============================================================================
# Log Message Schema
# ============================================================================

class LogMessage(BaseMessage):
    """
    Schema for log messages.
    
    Attributes:
        type: Message type (log_message)
        level: Log level
        logger: Logger name
        message: Log message
        context: Additional context data
    """
    type: Literal[MessageType.LOG_MESSAGE] = MessageType.LOG_MESSAGE
    level: LogLevel = Field(..., description="Log level")
    logger: str = Field(..., description="Logger name")
    message: str = Field(..., description="Log message")
    context: Dict[str, Any] = Field(default={}, description="Additional context")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "log_message",
                "timestamp": "2024-01-20T15:45:00Z",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "level": "info",
                "logger": "metagpt.agent",
                "message": "Agent initialized successfully",
                "context": {"agent_id": "arch_001"}
            }
        }


# ============================================================================
# Progress Update Schema
# ============================================================================

class ProgressUpdate(BaseMessage):
    """
    Schema for progress update messages.
    
    Attributes:
        type: Message type (progress_update)
        progress: Progress percentage (0-100)
        current_step: Current step description
        total_steps: Total number of steps
        eta_seconds: Estimated time remaining in seconds
    """
    type: Literal[MessageType.PROGRESS_UPDATE] = MessageType.PROGRESS_UPDATE
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_step: str = Field(..., description="Current step description")
    total_steps: int = Field(..., ge=1, description="Total number of steps")
    eta_seconds: Optional[float] = Field(None, ge=0, description="Estimated time remaining")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "progress_update",
                "timestamp": "2024-01-20T15:45:00Z",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "progress": 45.5,
                "current_step": "Code generation",
                "total_steps": 5,
                "eta_seconds": 120.5
            }
        }


# ============================================================================
# Execution Event Schemas
# ============================================================================

class ExecutionStart(BaseMessage):
    """
    Schema for execution start message.
    
    Attributes:
        type: Message type (execution_start)
        execution_type: Type of execution
        agents_count: Number of agents involved
    """
    type: Literal[MessageType.EXECUTION_START] = MessageType.EXECUTION_START
    execution_type: str = Field(..., description="Type of execution")
    agents_count: int = Field(..., ge=1, description="Number of agents")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "execution_start",
                "timestamp": "2024-01-20T15:45:00Z",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "execution_type": "full",
                "agents_count": 4
            }
        }


class ExecutionComplete(BaseMessage):
    """
    Schema for execution completion message.
    
    Attributes:
        type: Message type (execution_complete)
        status: Final execution status
        duration_seconds: Total execution duration
        output: Execution output/results
    """
    type: Literal[MessageType.EXECUTION_COMPLETE] = MessageType.EXECUTION_COMPLETE
    status: ExecutionStatus = Field(..., description="Final execution status")
    duration_seconds: float = Field(..., ge=0, description="Total duration")
    output: Dict[str, Any] = Field(default={}, description="Execution output")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "execution_complete",
                "timestamp": "2024-01-20T15:45:00Z",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "completed",
                "duration_seconds": 245.5,
                "output": {"files_created": 12, "tests_passed": 45}
            }
        }


# ============================================================================
# Connection Messages
# ============================================================================

class ConnectionAck(BaseModel):
    """
    Schema for connection acknowledgment message.
    
    Attributes:
        type: Message type (connection_ack)
        timestamp: Message timestamp
        connection_id: Unique connection identifier
        server_version: Server version
    """
    type: Literal[MessageType.CONNECTION_ACK] = MessageType.CONNECTION_ACK
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    connection_id: str = Field(..., description="Unique connection identifier")
    server_version: str = Field(..., description="Server version")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "connection_ack",
                "timestamp": "2024-01-20T15:45:00Z",
                "connection_id": "conn_550e8400",
                "server_version": "0.1.0"
            }
        }


class Heartbeat(BaseModel):
    """
    Schema for heartbeat message.
    
    Attributes:
        type: Message type (heartbeat)
        timestamp: Message timestamp
    """
    type: Literal[MessageType.HEARTBEAT] = MessageType.HEARTBEAT
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "heartbeat",
                "timestamp": "2024-01-20T15:45:00Z"
            }
        }


# ============================================================================
# Command Schema
# ============================================================================

class Command(BaseModel):
    """
    Schema for command messages from client.
    
    Attributes:
        type: Message type (command)
        timestamp: Message timestamp
        command: Command name
        parameters: Command parameters
    """
    type: Literal[MessageType.COMMAND] = MessageType.COMMAND
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    command: str = Field(..., description="Command name")
    parameters: Dict[str, Any] = Field(default={}, description="Command parameters")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "type": "command",
                "timestamp": "2024-01-20T15:45:00Z",
                "command": "pause_execution",
                "parameters": {"project_id": "550e8400-e29b-41d4-a716-446655440000"}
            }
        }


# ============================================================================
# Union Type for Message Discrimination
# ============================================================================

WebSocketMessage = Union[
    AgentMessage,
    StatusUpdate,
    FileUpdate,
    ErrorMessage,
    LogMessage,
    ProgressUpdate,
    ExecutionStart,
    ExecutionComplete,
    ConnectionAck,
    Heartbeat,
    Command,
]
"""
Union type for all WebSocket message types.

This type can be used for message discrimination and routing.
"""


# ============================================================================
# Message Wrapper Schema
# ============================================================================

class MessageWrapper(BaseModel):
    """
    Schema for wrapped WebSocket message with metadata.
    
    Attributes:
        message: The actual message (discriminated union)
        client_id: Client identifier
        sequence_number: Message sequence number
    """
    message: WebSocketMessage = Field(..., description="The actual message")
    client_id: str = Field(..., description="Client identifier")
    sequence_number: int = Field(..., ge=0, description="Message sequence number")

    class Config:
        """Pydantic configuration."""
        discriminator = "type"


# ============================================================================
# Subscription Schema
# ============================================================================

class SubscriptionRequest(BaseModel):
    """
    Schema for WebSocket subscription request.
    
    Attributes:
        project_id: Project ID to subscribe to
        execution_id: Optional execution ID to subscribe to
        message_types: Optional list of message types to receive
    """
    project_id: str = Field(..., description="Project ID to subscribe to")
    execution_id: Optional[str] = Field(None, description="Optional execution ID")
    message_types: Optional[List[MessageType]] = Field(
        None,
        description="Optional message types to receive"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001",
                "message_types": ["agent_message", "status_update", "error_message"]
            }
        }


class UnsubscriptionRequest(BaseModel):
    """
    Schema for WebSocket unsubscription request.
    
    Attributes:
        project_id: Project ID to unsubscribe from
        execution_id: Optional execution ID to unsubscribe from
    """
    project_id: str = Field(..., description="Project ID to unsubscribe from")
    execution_id: Optional[str] = Field(None, description="Optional execution ID")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }
