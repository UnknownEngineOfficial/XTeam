"""
WebSocket API Endpoints

This module provides WebSocket endpoints for real-time communication with clients.
Handles connection management, message routing, and event broadcasting.

Features:
- WebSocket connection with JWT authentication
- Message routing and handling
- Event subscription and filtering
- Connection lifecycle management
- Heartbeat and keep-alive
- Error handling and recovery
"""

import logging
import json
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.websocket.connection_manager import (
    get_connection_manager,
    ConnectionManager,
)
from app.websocket.message_handler import (
    get_message_handler,
    MessageHandler,
    MessageType,
)
from app.metagpt_integration.streaming import (
    get_streaming_handler,
    StreamingHandler,
    EventType,
    EventFilter,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


# ============================================================================
# WebSocket Authentication
# ============================================================================

async def get_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """
    Authenticate user from WebSocket token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object or None if invalid
    """
    from sqlalchemy import select
    
    payload = verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time communication.
    
    Query Parameters:
        token: JWT authentication token (required)
        
    Connection Flow:
        1. Authenticate user with JWT token
        2. Accept WebSocket connection
        3. Register connection with manager
        4. Listen for incoming messages
        5. Route messages to handlers
        6. Send responses back to client
        7. Clean up on disconnect
        
    Message Format:
        {
            "type": "message_type",
            "payload": {...}
        }
        
    Response Format:
        {
            "success": true/false,
            "message_type": "...",
            "data": {...},
            "error": "...",
            "timestamp": "..."
        }
    """
    # Authenticate user
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        logger.warning("WebSocket connection rejected: Invalid token")
        return

    # Generate connection ID
    connection_id = f"ws_{uuid4().hex[:12]}"

    # Get managers
    conn_manager = get_connection_manager()
    msg_handler = get_message_handler(db, settings)
    streaming_handler = await get_streaming_handler()

    try:
        # Accept connection
        conn_info = await conn_manager.connect(
            connection_id=connection_id,
            websocket=websocket,
            user_id=str(user.id),
        )

        logger.info(f"WebSocket connected: {connection_id} (user: {user.id})")

        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connection_ack",
            "connection_id": connection_id,
            "user_id": str(user.id),
            "timestamp": conn_info.connected_at.isoformat(),
        })

        # Listen for messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()

                # Extract message type and payload
                message_type = data.get("type")
                payload = data.get("payload", {})

                if not message_type:
                    await websocket.send_json({
                        "success": False,
                        "error": "Missing message type",
                    })
                    continue

                logger.debug(f"Received message {message_type} from {connection_id}")

                # Handle message
                response = await msg_handler.handle(
                    message_type=message_type,
                    payload=payload,
                    user=user,
                )

                # Send response
                await websocket.send_json(response.to_dict())

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {connection_id}")
                await websocket.send_json({
                    "success": False,
                    "error": "Invalid JSON format",
                })
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                await websocket.send_json({
                    "success": False,
                    "error": f"Internal error: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        await conn_manager.disconnect(connection_id)

    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        try:
            await conn_manager.disconnect(connection_id)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")


@router.websocket("/ws/project/{project_id}")
async def websocket_project_endpoint(
    websocket: WebSocket,
    project_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for project-specific real-time communication.
    
    Path Parameters:
        project_id: Project identifier
        
    Query Parameters:
        token: JWT authentication token (required)
        
    Features:
        - Project-scoped message routing
        - Automatic subscription to project events
        - Project-specific event filtering
    """
    # Authenticate user
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        logger.warning("WebSocket connection rejected: Invalid token")
        return

    # Verify user has access to project
    from app.services.project_service import get_project_service
    project_service = get_project_service(db)
    project = await project_service.get_project(project_id, str(user.id))
    if not project:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Project not found")
        logger.warning(f"WebSocket connection rejected: Project {project_id} not found")
        return

    # Generate connection ID
    connection_id = f"ws_proj_{uuid4().hex[:12]}"

    # Get managers
    conn_manager = get_connection_manager()
    msg_handler = get_message_handler(db, settings)
    streaming_handler = await get_streaming_handler()

    try:
        # Accept connection with project context
        conn_info = await conn_manager.connect(
            connection_id=connection_id,
            websocket=websocket,
            user_id=str(user.id),
            project_id=project_id,
        )

        logger.info(
            f"WebSocket project connected: {connection_id} "
            f"(user: {user.id}, project: {project_id})"
        )

        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connection_ack",
            "connection_id": connection_id,
            "user_id": str(user.id),
            "project_id": project_id,
            "timestamp": conn_info.connected_at.isoformat(),
        })

        # Subscribe to project events
        async def on_streaming_event(event):
            """Handle streaming events for this connection."""
            try:
                await websocket.send_json({
                    "type": "event",
                    "event": event.to_dict(),
                })
            except Exception as e:
                logger.error(f"Error sending event to {connection_id}: {e}")

        # Create filter for project events
        event_filter = EventFilter(
            project_ids={project_id},
        )

        # Subscribe to streaming events
        subscriber = await streaming_handler.subscribe(
            subscriber_id=connection_id,
            callback=on_streaming_event,
            event_filter=event_filter,
        )

        # Listen for messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()

                # Extract message type and payload
                message_type = data.get("type")
                payload = data.get("payload", {})

                if not message_type:
                    await websocket.send_json({
                        "success": False,
                        "error": "Missing message type",
                    })
                    continue

                # Add project context to payload
                payload["project_id"] = project_id

                logger.debug(
                    f"Received message {message_type} from {connection_id} "
                    f"(project: {project_id})"
                )

                # Handle message
                response = await msg_handler.handle(
                    message_type=message_type,
                    payload=payload,
                    user=user,
                )

                # Send response
                await websocket.send_json(response.to_dict())

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {connection_id}")
                await websocket.send_json({
                    "success": False,
                    "error": "Invalid JSON format",
                })
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                await websocket.send_json({
                    "success": False,
                    "error": f"Internal error: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket project disconnected: {connection_id}")
        await streaming_handler.unsubscribe(connection_id)
        await conn_manager.disconnect(connection_id)

    except Exception as e:
        logger.error(f"WebSocket project error for {connection_id}: {e}")
        try:
            await streaming_handler.unsubscribe(connection_id)
            await conn_manager.disconnect(connection_id)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")


@router.websocket("/ws/execution/{execution_id}")
async def websocket_execution_endpoint(
    websocket: WebSocket,
    execution_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for execution-specific real-time communication.
    
    Path Parameters:
        execution_id: Execution identifier
        
    Query Parameters:
        token: JWT authentication token (required)
        
    Features:
        - Execution-scoped message routing
        - Automatic subscription to execution events
        - Real-time log streaming
        - Progress updates
    """
    from uuid import UUID
    from app.models.execution import Execution

    # Authenticate user
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        logger.warning("WebSocket connection rejected: Invalid token")
        return

    # Verify user has access to execution
    try:
        execution = await db.get(Execution, UUID(execution_id))
        if not execution or execution.user_id != user.id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Execution not found")
            logger.warning(f"WebSocket connection rejected: Execution {execution_id} not found")
            return
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid execution ID")
        logger.warning(f"WebSocket connection rejected: Invalid execution ID - {e}")
        return

    # Generate connection ID
    connection_id = f"ws_exec_{uuid4().hex[:12]}"

    # Get managers
    conn_manager = get_connection_manager()
    msg_handler = get_message_handler(db, settings)
    streaming_handler = await get_streaming_handler()

    try:
        # Accept connection with execution context
        conn_info = await conn_manager.connect(
            connection_id=connection_id,
            websocket=websocket,
            user_id=str(user.id),
            project_id=str(execution.project_id),
        )

        logger.info(
            f"WebSocket execution connected: {connection_id} "
            f"(user: {user.id}, execution: {execution_id})"
        )

        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connection_ack",
            "connection_id": connection_id,
            "user_id": str(user.id),
            "execution_id": execution_id,
            "project_id": str(execution.project_id),
            "timestamp": conn_info.connected_at.isoformat(),
        })

        # Subscribe to execution events
        async def on_streaming_event(event):
            """Handle streaming events for this connection."""
            try:
                await websocket.send_json({
                    "type": "event",
                    "event": event.to_dict(),
                })
            except Exception as e:
                logger.error(f"Error sending event to {connection_id}: {e}")

        # Create filter for execution events
        event_filter = EventFilter(
            execution_ids={execution_id},
        )

        # Subscribe to streaming events
        subscriber = await streaming_handler.subscribe(
            subscriber_id=connection_id,
            callback=on_streaming_event,
            event_filter=event_filter,
        )

        # Listen for messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()

                # Extract message type and payload
                message_type = data.get("type")
                payload = data.get("payload", {})

                if not message_type:
                    await websocket.send_json({
                        "success": False,
                        "error": "Missing message type",
                    })
                    continue

                # Add execution context to payload
                payload["execution_id"] = execution_id
                payload["project_id"] = str(execution.project_id)

                logger.debug(
                    f"Received message {message_type} from {connection_id} "
                    f"(execution: {execution_id})"
                )

                # Handle message
                response = await msg_handler.handle(
                    message_type=message_type,
                    payload=payload,
                    user=user,
                )

                # Send response
                await websocket.send_json(response.to_dict())

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {connection_id}")
                await websocket.send_json({
                    "success": False,
                    "error": "Invalid JSON format",
                })
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                await websocket.send_json({
                    "success": False,
                    "error": f"Internal error: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket execution disconnected: {connection_id}")
        await streaming_handler.unsubscribe(connection_id)
        await conn_manager.disconnect(connection_id)

    except Exception as e:
        logger.error(f"WebSocket execution error for {connection_id}: {e}")
        try:
            await streaming_handler.unsubscribe(connection_id)
            await conn_manager.disconnect(connection_id)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")


# ============================================================================
# Health Check Endpoints
# ============================================================================

@router.get("/health")
async def websocket_health():
    """
    Check WebSocket system health.
    
    Returns:
        Health status with connection statistics
    """
    conn_manager = get_connection_manager()
    streaming_handler = await get_streaming_handler()

    return {
        "status": "healthy",
        "connections": conn_manager.get_metrics(),
        "streaming": streaming_handler.get_metrics(),
    }


@router.get("/connections")
async def get_connections():
    """
    Get all active WebSocket connections.
    
    Returns:
        List of active connections with details
    """
    conn_manager = get_connection_manager()
    return {
        "connections": conn_manager.get_all_connections(),
        "metrics": conn_manager.get_metrics(),
    }


@router.get("/connections/user/{user_id}")
async def get_user_connections(user_id: str):
    """
    Get all WebSocket connections for a user.
    
    Path Parameters:
        user_id: User identifier
        
    Returns:
        List of user's connections
    """
    conn_manager = get_connection_manager()
    return {
        "user_id": user_id,
        "connections": conn_manager.get_user_connections(user_id),
        "count": conn_manager.get_user_connection_count(user_id),
    }


@router.get("/connections/project/{project_id}")
async def get_project_connections(project_id: str):
    """
    Get all WebSocket connections for a project.
    
    Path Parameters:
        project_id: Project identifier
        
    Returns:
        List of project's connections
    """
    conn_manager = get_connection_manager()
    return {
        "project_id": project_id,
        "connections": conn_manager.get_project_connections(project_id),
        "count": conn_manager.get_project_connection_count(project_id),
    }
