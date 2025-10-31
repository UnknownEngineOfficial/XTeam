"""
WebSocket Connection Manager Module

This module manages active WebSocket connections, organizing them by user
and project. It provides methods for connecting, disconnecting, and sending
messages to specific users, projects, or broadcast to all connections.

Features:
- Connection tracking by user and project
- Targeted message delivery (user, project, broadcast)
- Connection pooling and lifecycle management
- Automatic cleanup on disconnect
- Connection statistics and monitoring
- Graceful error handling
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from fastapi import WebSocket
from collections import defaultdict


logger = logging.getLogger(__name__)


class ConnectionInfo:
    """
    Information about a WebSocket connection.
    
    Attributes:
        connection_id: Unique connection identifier
        websocket: WebSocket connection object
        user_id: Associated user ID
        project_id: Associated project ID
        connected_at: Connection timestamp
        last_activity: Last activity timestamp
        message_count: Number of messages sent
    """

    def __init__(
        self,
        connection_id: str,
        websocket: WebSocket,
        user_id: str,
        project_id: Optional[str] = None,
    ):
        """Initialize connection info."""
        self.connection_id = connection_id
        self.websocket = websocket
        self.user_id = user_id
        self.project_id = project_id
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.message_count = 0

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def increment_message_count(self) -> None:
        """Increment message count."""
        self.message_count += 1

    def get_info(self) -> Dict:
        """Get connection information."""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "duration_seconds": (datetime.utcnow() - self.connected_at).total_seconds(),
        }


class ConnectionManager:
    """
    Manages active WebSocket connections.
    
    Organizes connections by user and project, providing methods for
    targeted message delivery and connection lifecycle management.
    """

    def __init__(self):
        """Initialize connection manager."""
        # Connections indexed by connection_id
        self.connections: Dict[str, ConnectionInfo] = {}
        
        # Connections indexed by user_id
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # Connections indexed by project_id
        self.project_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # Metrics
        self.metrics = {
            "total_connections": 0,
            "total_disconnections": 0,
            "total_messages_sent": 0,
            "total_errors": 0,
        }

    async def connect(
        self,
        connection_id: str,
        websocket: WebSocket,
        user_id: str,
        project_id: Optional[str] = None,
    ) -> ConnectionInfo:
        """
        Register a new WebSocket connection.
        
        Args:
            connection_id: Unique connection identifier
            websocket: WebSocket connection object
            user_id: Associated user ID
            project_id: Associated project ID (optional)
            
        Returns:
            ConnectionInfo object
            
        Raises:
            ValueError: If connection_id already exists
        """
        if connection_id in self.connections:
            raise ValueError(f"Connection {connection_id} already exists")

        # Accept the connection
        await websocket.accept()

        # Create connection info
        conn_info = ConnectionInfo(connection_id, websocket, user_id, project_id)

        # Store connection
        self.connections[connection_id] = conn_info
        self.user_connections[user_id].add(connection_id)
        if project_id:
            self.project_connections[project_id].add(connection_id)

        # Update metrics
        self.metrics["total_connections"] += 1

        logger.info(
            f"Connection {connection_id} established for user {user_id} "
            f"(project: {project_id or 'none'})"
        )

        return conn_info

    async def disconnect(self, connection_id: str) -> bool:
        """
        Unregister a WebSocket connection.
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            True if disconnected, False if not found
        """
        conn_info = self.connections.get(connection_id)
        if not conn_info:
            return False

        try:
            # Close the connection
            await conn_info.websocket.close()
        except Exception as e:
            logger.warning(f"Error closing connection {connection_id}: {e}")

        # Remove from all indexes
        del self.connections[connection_id]
        self.user_connections[conn_info.user_id].discard(connection_id)
        if conn_info.project_id:
            self.project_connections[conn_info.project_id].discard(connection_id)

        # Clean up empty sets
        if not self.user_connections[conn_info.user_id]:
            del self.user_connections[conn_info.user_id]
        if conn_info.project_id and not self.project_connections[conn_info.project_id]:
            del self.project_connections[conn_info.project_id]

        # Update metrics
        self.metrics["total_disconnections"] += 1

        logger.info(
            f"Connection {connection_id} closed for user {conn_info.user_id} "
            f"(project: {conn_info.project_id or 'none'})"
        )

        return True

    async def send_to_connection(
        self,
        connection_id: str,
        data: Dict,
    ) -> bool:
        """
        Send message to a specific connection.
        
        Args:
            connection_id: Connection identifier
            data: Message data to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        conn_info = self.connections.get(connection_id)
        if not conn_info:
            logger.warning(f"Connection {connection_id} not found")
            return False

        try:
            await conn_info.websocket.send_json(data)
            conn_info.increment_message_count()
            conn_info.update_activity()
            self.metrics["total_messages_sent"] += 1
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            self.metrics["total_errors"] += 1
            # Attempt to disconnect on error
            await self.disconnect(connection_id)
            return False

    async def send_to_user(
        self,
        user_id: str,
        data: Dict,
        exclude_connection_id: Optional[str] = None,
    ) -> int:
        """
        Send message to all connections of a user.
        
        Args:
            user_id: User identifier
            data: Message data to send
            exclude_connection_id: Connection to exclude (optional)
            
        Returns:
            Number of messages sent successfully
        """
        connection_ids = self.user_connections.get(user_id, set()).copy()
        sent_count = 0

        for connection_id in connection_ids:
            if exclude_connection_id and connection_id == exclude_connection_id:
                continue

            if await self.send_to_connection(connection_id, data):
                sent_count += 1

        if sent_count > 0:
            logger.debug(f"Sent message to {sent_count} connection(s) for user {user_id}")

        return sent_count

    async def send_to_project(
        self,
        project_id: str,
        data: Dict,
        exclude_user_id: Optional[str] = None,
    ) -> int:
        """
        Send message to all connections of a project.
        
        Args:
            project_id: Project identifier
            data: Message data to send
            exclude_user_id: User to exclude (optional)
            
        Returns:
            Number of messages sent successfully
        """
        connection_ids = self.project_connections.get(project_id, set()).copy()
        sent_count = 0

        for connection_id in connection_ids:
            conn_info = self.connections.get(connection_id)
            if not conn_info:
                continue

            if exclude_user_id and conn_info.user_id == exclude_user_id:
                continue

            if await self.send_to_connection(connection_id, data):
                sent_count += 1

        if sent_count > 0:
            logger.debug(f"Sent message to {sent_count} connection(s) for project {project_id}")

        return sent_count

    async def broadcast(
        self,
        data: Dict,
        exclude_user_id: Optional[str] = None,
        exclude_connection_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast message to all connections.
        
        Args:
            data: Message data to send
            exclude_user_id: User to exclude (optional)
            exclude_connection_id: Connection to exclude (optional)
            
        Returns:
            Number of messages sent successfully
        """
        connection_ids = list(self.connections.keys())
        sent_count = 0

        for connection_id in connection_ids:
            if exclude_connection_id and connection_id == exclude_connection_id:
                continue

            conn_info = self.connections.get(connection_id)
            if not conn_info:
                continue

            if exclude_user_id and conn_info.user_id == exclude_user_id:
                continue

            if await self.send_to_connection(connection_id, data):
                sent_count += 1

        if sent_count > 0:
            logger.debug(f"Broadcast message to {sent_count} connection(s)")

        return sent_count

    async def send_to_users(
        self,
        user_ids: List[str],
        data: Dict,
    ) -> int:
        """
        Send message to multiple users.
        
        Args:
            user_ids: List of user identifiers
            data: Message data to send
            
        Returns:
            Number of messages sent successfully
        """
        sent_count = 0
        for user_id in user_ids:
            sent_count += await self.send_to_user(user_id, data)
        return sent_count

    async def send_to_projects(
        self,
        project_ids: List[str],
        data: Dict,
    ) -> int:
        """
        Send message to multiple projects.
        
        Args:
            project_ids: List of project identifiers
            data: Message data to send
            
        Returns:
            Number of messages sent successfully
        """
        sent_count = 0
        for project_id in project_ids:
            sent_count += await self.send_to_project(project_id, data)
        return sent_count

    def get_connection_info(self, connection_id: str) -> Optional[Dict]:
        """
        Get information about a connection.
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            Connection info dictionary or None if not found
        """
        conn_info = self.connections.get(connection_id)
        return conn_info.get_info() if conn_info else None

    def get_user_connections(self, user_id: str) -> List[Dict]:
        """
        Get all connections for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of connection info dictionaries
        """
        connection_ids = self.user_connections.get(user_id, set())
        return [
            self.connections[cid].get_info()
            for cid in connection_ids
            if cid in self.connections
        ]

    def get_project_connections(self, project_id: str) -> List[Dict]:
        """
        Get all connections for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of connection info dictionaries
        """
        connection_ids = self.project_connections.get(project_id, set())
        return [
            self.connections[cid].get_info()
            for cid in connection_ids
            if cid in self.connections
        ]

    def get_all_connections(self) -> List[Dict]:
        """
        Get all active connections.
        
        Returns:
            List of connection info dictionaries
        """
        return [conn_info.get_info() for conn_info in self.connections.values()]

    def get_user_count(self) -> int:
        """Get number of connected users."""
        return len(self.user_connections)

    def get_project_count(self) -> int:
        """Get number of projects with active connections."""
        return len(self.project_connections)

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connections)

    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get number of connections for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of connections
        """
        return len(self.user_connections.get(user_id, set()))

    def get_project_connection_count(self, project_id: str) -> int:
        """
        Get number of connections for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Number of connections
        """
        return len(self.project_connections.get(project_id, set()))

    def get_metrics(self) -> Dict:
        """
        Get connection manager metrics.
        
        Returns:
            Dictionary with metrics
        """
        return {
            **self.metrics,
            "active_connections": self.get_connection_count(),
            "active_users": self.get_user_count(),
            "active_projects": self.get_project_count(),
        }

    async def cleanup_inactive_connections(self, timeout_seconds: int = 3600) -> int:
        """
        Clean up inactive connections.
        
        Args:
            timeout_seconds: Inactivity timeout in seconds
            
        Returns:
            Number of connections cleaned up
        """
        now = datetime.utcnow()
        inactive_connections = []

        for connection_id, conn_info in self.connections.items():
            inactivity_duration = (now - conn_info.last_activity).total_seconds()
            if inactivity_duration > timeout_seconds:
                inactive_connections.append(connection_id)

        cleaned_count = 0
        for connection_id in inactive_connections:
            if await self.disconnect(connection_id):
                cleaned_count += 1
                logger.info(f"Cleaned up inactive connection {connection_id}")

        return cleaned_count

    async def disconnect_user(self, user_id: str) -> int:
        """
        Disconnect all connections for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of connections disconnected
        """
        connection_ids = self.user_connections.get(user_id, set()).copy()
        disconnected_count = 0

        for connection_id in connection_ids:
            if await self.disconnect(connection_id):
                disconnected_count += 1

        logger.info(f"Disconnected {disconnected_count} connection(s) for user {user_id}")
        return disconnected_count

    async def disconnect_project(self, project_id: str) -> int:
        """
        Disconnect all connections for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Number of connections disconnected
        """
        connection_ids = self.project_connections.get(project_id, set()).copy()
        disconnected_count = 0

        for connection_id in connection_ids:
            if await self.disconnect(connection_id):
                disconnected_count += 1

        logger.info(f"Disconnected {disconnected_count} connection(s) for project {project_id}")
        return disconnected_count

    async def disconnect_all(self) -> int:
        """
        Disconnect all connections.
        
        Returns:
            Number of connections disconnected
        """
        connection_ids = list(self.connections.keys())
        disconnected_count = 0

        for connection_id in connection_ids:
            if await self.disconnect(connection_id):
                disconnected_count += 1

        logger.info(f"Disconnected all {disconnected_count} connection(s)")
        return disconnected_count


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get or create global connection manager instance.
    
    Returns:
        ConnectionManager instance
    """
    global _connection_manager

    if _connection_manager is None:
        _connection_manager = ConnectionManager()
        logger.info("Connection manager initialized")

    return _connection_manager


# Global instance for direct import
connection_manager = get_connection_manager()


async def close_connection_manager() -> None:
    """Close global connection manager instance."""
    global _connection_manager

    if _connection_manager:
        await _connection_manager.disconnect_all()
        _connection_manager = None
        logger.info("Connection manager closed")
