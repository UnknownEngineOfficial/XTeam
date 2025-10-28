"""
Streaming Handler Module

This module provides real-time streaming of agent outputs including logs,
file changes, progress updates, and execution events to WebSocket clients.

Features:
- Event-based streaming with multiple event types
- Async event emission with buffering
- Subscriber management for targeted delivery
- Event filtering and transformation
- Metrics and monitoring
- Graceful shutdown handling
"""

import json
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import UUID


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Streaming event types."""
    # Agent events
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    
    # Execution events
    EXECUTION_START = "execution_start"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_COMPLETE = "execution_complete"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"
    
    # Log events
    LOG_MESSAGE = "log_message"
    LOG_BATCH = "log_batch"
    
    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_BATCH = "file_batch"
    
    # Status events
    STATUS_UPDATE = "status_update"
    PROGRESS_UPDATE = "progress_update"
    
    # System events
    HEARTBEAT = "heartbeat"
    CONNECTION_ACK = "connection_ack"
    ERROR = "error"


class EventPriority(int, Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class StreamEvent:
    """
    Represents a streaming event.
    
    Attributes:
        event_type: Type of event
        data: Event data/payload
        timestamp: Event creation timestamp
        source: Source of event (e.g., agent name, module)
        execution_id: Associated execution ID
        project_id: Associated project ID
        priority: Event priority
        metadata: Additional metadata
    """
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    execution_id: Optional[str] = None
    project_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "execution_id": self.execution_id,
            "project_id": self.project_id,
            "priority": self.priority.value,
            "metadata": self.metadata or {},
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class EventFilter:
    """
    Filters events based on criteria.
    
    Allows filtering by event type, source, execution ID, project ID, etc.
    """

    def __init__(
        self,
        event_types: Optional[Set[EventType]] = None,
        sources: Optional[Set[str]] = None,
        execution_ids: Optional[Set[str]] = None,
        project_ids: Optional[Set[str]] = None,
        min_priority: EventPriority = EventPriority.LOW,
    ):
        """
        Initialize event filter.
        
        Args:
            event_types: Set of event types to include (None = all)
            sources: Set of sources to include (None = all)
            execution_ids: Set of execution IDs to include (None = all)
            project_ids: Set of project IDs to include (None = all)
            min_priority: Minimum event priority to include
        """
        self.event_types = event_types
        self.sources = sources
        self.execution_ids = execution_ids
        self.project_ids = project_ids
        self.min_priority = min_priority

    def matches(self, event: StreamEvent) -> bool:
        """
        Check if event matches filter criteria.
        
        Args:
            event: Event to check
            
        Returns:
            True if event matches all criteria
        """
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False

        # Check source
        if self.sources and event.source not in self.sources:
            return False

        # Check execution ID
        if self.execution_ids and event.execution_id not in self.execution_ids:
            return False

        # Check project ID
        if self.project_ids and event.project_id not in self.project_ids:
            return False

        # Check priority
        if event.priority.value < self.min_priority.value:
            return False

        return True


class Subscriber:
    """
    Represents a subscriber to streaming events.
    
    Attributes:
        subscriber_id: Unique subscriber identifier
        callback: Async callback function to receive events
        filter: Event filter for this subscriber
        active: Whether subscriber is active
    """

    def __init__(
        self,
        subscriber_id: str,
        callback: Callable[[StreamEvent], Any],
        event_filter: Optional[EventFilter] = None,
    ):
        """Initialize subscriber."""
        self.subscriber_id = subscriber_id
        self.callback = callback
        self.filter = event_filter or EventFilter()
        self.active = True
        self.created_at = datetime.utcnow()
        self.events_received = 0

    async def send_event(self, event: StreamEvent) -> bool:
        """
        Send event to subscriber if it matches filter.
        
        Args:
            event: Event to send
            
        Returns:
            True if event was sent, False if filtered out or error
        """
        if not self.active:
            return False

        if not self.filter.matches(event):
            return False

        try:
            result = self.callback(event)
            if asyncio.iscoroutine(result):
                await result
            self.events_received += 1
            return True
        except Exception as e:
            logger.error(f"Error sending event to subscriber {self.subscriber_id}: {e}")
            return False

    def deactivate(self) -> None:
        """Deactivate subscriber."""
        self.active = False


class StreamingHandler:
    """
    Handles real-time streaming of agent outputs to subscribers.
    
    Manages event emission, subscriber registration, buffering, and delivery.
    Supports multiple event types and subscriber filtering.
    """

    def __init__(self, buffer_size: int = 1000, batch_timeout_ms: int = 100):
        """
        Initialize streaming handler.
        
        Args:
            buffer_size: Maximum number of events to buffer
            batch_timeout_ms: Timeout for batching events in milliseconds
        """
        self.buffer_size = buffer_size
        self.batch_timeout_ms = batch_timeout_ms
        self.subscribers: Dict[str, Subscriber] = {}
        self.event_buffer: List[StreamEvent] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.metrics = {
            "total_events": 0,
            "total_subscribers": 0,
            "events_by_type": {},
            "events_by_source": {},
        }
        self._lock = asyncio.Lock()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the streaming handler."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Streaming handler started")

    async def stop(self) -> None:
        """Stop the streaming handler."""
        if not self._running:
            return

        self._running = False

        # Flush remaining events
        await self._flush_buffer()

        # Cancel processor task
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        logger.info("Streaming handler stopped")

    async def emit(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str,
        execution_id: Optional[str] = None,
        project_id: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emit a streaming event.
        
        Args:
            event_type: Type of event
            data: Event data/payload
            source: Source of event
            execution_id: Associated execution ID
            project_id: Associated project ID
            priority: Event priority
            metadata: Additional metadata
        """
        if not self._running:
            logger.warning("Streaming handler not running, event dropped")
            return

        event = StreamEvent(
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            source=source,
            execution_id=execution_id,
            project_id=project_id,
            priority=priority,
            metadata=metadata,
        )

        await self.event_queue.put(event)

    async def subscribe(
        self,
        subscriber_id: str,
        callback: Callable[[StreamEvent], Any],
        event_filter: Optional[EventFilter] = None,
    ) -> Subscriber:
        """
        Subscribe to streaming events.
        
        Args:
            subscriber_id: Unique subscriber identifier
            callback: Async callback function to receive events
            event_filter: Optional event filter
            
        Returns:
            Subscriber object
        """
        async with self._lock:
            subscriber = Subscriber(subscriber_id, callback, event_filter)
            self.subscribers[subscriber_id] = subscriber
            self.metrics["total_subscribers"] = len(self.subscribers)
            logger.info(f"Subscriber {subscriber_id} registered")
            return subscriber

    async def unsubscribe(self, subscriber_id: str) -> bool:
        """
        Unsubscribe from streaming events.
        
        Args:
            subscriber_id: Subscriber identifier
            
        Returns:
            True if unsubscribed, False if not found
        """
        async with self._lock:
            if subscriber_id in self.subscribers:
                subscriber = self.subscribers.pop(subscriber_id)
                subscriber.deactivate()
                self.metrics["total_subscribers"] = len(self.subscribers)
                logger.info(f"Subscriber {subscriber_id} unregistered")
                return True
            return False

    async def _process_events(self) -> None:
        """Process events from queue and deliver to subscribers."""
        try:
            while self._running:
                try:
                    # Get event with timeout
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.batch_timeout_ms / 1000,
                    )

                    # Add to buffer
                    async with self._lock:
                        self.event_buffer.append(event)

                        # Update metrics
                        self.metrics["total_events"] += 1
                        event_type_key = event.event_type.value
                        self.metrics["events_by_type"][event_type_key] = \
                            self.metrics["events_by_type"].get(event_type_key, 0) + 1
                        self.metrics["events_by_source"][event.source] = \
                            self.metrics["events_by_source"].get(event.source, 0) + 1

                        # Flush if buffer is full
                        if len(self.event_buffer) >= self.buffer_size:
                            await self._flush_buffer_unsafe()

                except asyncio.TimeoutError:
                    # Flush buffer on timeout
                    async with self._lock:
                        if self.event_buffer:
                            await self._flush_buffer_unsafe()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in event processor: {e}")

    async def _flush_buffer(self) -> None:
        """Flush event buffer to subscribers."""
        async with self._lock:
            await self._flush_buffer_unsafe()

    async def _flush_buffer_unsafe(self) -> None:
        """
        Flush event buffer to subscribers (must be called with lock held).
        """
        if not self.event_buffer:
            return

        # Sort by priority (higher priority first)
        sorted_events = sorted(
            self.event_buffer,
            key=lambda e: e.priority.value,
            reverse=True,
        )

        # Deliver to subscribers
        for event in sorted_events:
            tasks = []
            for subscriber in self.subscribers.values():
                task = subscriber.send_event(event)
                if asyncio.iscoroutine(task):
                    tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        self.event_buffer.clear()

    async def emit_log(
        self,
        message: str,
        level: str = "INFO",
        source: str = "agent",
        execution_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """
        Emit a log message event.
        
        Args:
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            source: Source of log
            execution_id: Associated execution ID
            project_id: Associated project ID
        """
        await self.emit(
            event_type=EventType.LOG_MESSAGE,
            data={
                "message": message,
                "level": level,
            },
            source=source,
            execution_id=execution_id,
            project_id=project_id,
        )

    async def emit_file_change(
        self,
        event_type: EventType,
        file_path: str,
        content: Optional[str] = None,
        source: str = "file_handler",
        execution_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """
        Emit a file change event.
        
        Args:
            event_type: Type of file event (CREATED, MODIFIED, DELETED)
            file_path: Path to file
            content: File content (for CREATED/MODIFIED)
            source: Source of event
            execution_id: Associated execution ID
            project_id: Associated project ID
        """
        await self.emit(
            event_type=event_type,
            data={
                "file_path": file_path,
                "content": content,
            },
            source=source,
            execution_id=execution_id,
            project_id=project_id,
            priority=EventPriority.HIGH,
        )

    async def emit_progress(
        self,
        progress: int,
        stage: str,
        message: str = "",
        source: str = "agent",
        execution_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """
        Emit a progress update event.
        
        Args:
            progress: Progress percentage (0-100)
            stage: Current stage/phase
            message: Optional progress message
            source: Source of event
            execution_id: Associated execution ID
            project_id: Associated project ID
        """
        await self.emit(
            event_type=EventType.PROGRESS_UPDATE,
            data={
                "progress": max(0, min(100, progress)),
                "stage": stage,
                "message": message,
            },
            source=source,
            execution_id=execution_id,
            project_id=project_id,
            priority=EventPriority.HIGH,
        )

    async def emit_status(
        self,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        source: str = "agent",
        execution_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """
        Emit a status update event.
        
        Args:
            status: Status string
            details: Optional status details
            source: Source of event
            execution_id: Associated execution ID
            project_id: Associated project ID
        """
        await self.emit(
            event_type=EventType.STATUS_UPDATE,
            data={
                "status": status,
                "details": details or {},
            },
            source=source,
            execution_id=execution_id,
            project_id=project_id,
        )

    async def emit_error(
        self,
        error_message: str,
        error_type: str = "unknown",
        source: str = "agent",
        execution_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """
        Emit an error event.
        
        Args:
            error_message: Error message
            error_type: Type of error
            source: Source of event
            execution_id: Associated execution ID
            project_id: Associated project ID
        """
        await self.emit(
            event_type=EventType.ERROR,
            data={
                "error_message": error_message,
                "error_type": error_type,
            },
            source=source,
            execution_id=execution_id,
            project_id=project_id,
            priority=EventPriority.CRITICAL,
        )

    async def emit_heartbeat(self) -> None:
        """Emit a heartbeat event."""
        await self.emit(
            event_type=EventType.HEARTBEAT,
            data={"timestamp": datetime.utcnow().isoformat()},
            source="system",
            priority=EventPriority.LOW,
        )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get streaming handler metrics.
        
        Returns:
            Dictionary with metrics
        """
        return {
            **self.metrics,
            "active_subscribers": len(self.subscribers),
            "buffered_events": len(self.event_buffer),
            "queue_size": self.event_queue.qsize(),
        }

    def get_subscriber_info(self, subscriber_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a subscriber.
        
        Args:
            subscriber_id: Subscriber identifier
            
        Returns:
            Dictionary with subscriber info or None if not found
        """
        subscriber = self.subscribers.get(subscriber_id)
        if not subscriber:
            return None

        return {
            "subscriber_id": subscriber_id,
            "active": subscriber.active,
            "created_at": subscriber.created_at.isoformat(),
            "events_received": subscriber.events_received,
        }

    async def get_all_subscribers(self) -> List[Dict[str, Any]]:
        """
        Get information about all subscribers.
        
        Returns:
            List of subscriber info dictionaries
        """
        return [
            self.get_subscriber_info(sub_id)
            for sub_id in self.subscribers.keys()
        ]


# Global streaming handler instance
_streaming_handler: Optional[StreamingHandler] = None


async def get_streaming_handler() -> StreamingHandler:
    """
    Get or create global streaming handler instance.
    
    Returns:
        StreamingHandler instance
    """
    global _streaming_handler

    if _streaming_handler is None:
        _streaming_handler = StreamingHandler()
        await _streaming_handler.start()

    return _streaming_handler


async def close_streaming_handler() -> None:
    """Close global streaming handler instance."""
    global _streaming_handler

    if _streaming_handler:
        await _streaming_handler.stop()
        _streaming_handler = None
