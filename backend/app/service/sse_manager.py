# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

"""SSE Connection Manager for tracking and managing Server-Sent Events connections."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("sse_manager")


@dataclass
class SSEConnection:
    """Represents an active SSE connection."""

    connection_id: str
    project_id: str
    user_id: str | None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True


class SSEConnectionManager:
    """Manages SSE connections for the application.

    Tracks active connections per project and provides methods for
    adding, removing, and broadcasting to connections.
    """

    def __init__(self):
        """Initialize the SSE connection manager."""
        self._connections: dict[str, SSEConnection] = {}
        self._project_connections: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def add_connection(
        self,
        connection_id: str,
        project_id: str,
        user_id: str | None = None,
    ) -> SSEConnection:
        """Add a new SSE connection."""
        async with self._lock:
            connection = SSEConnection(
                connection_id=connection_id,
                project_id=project_id,
                user_id=user_id,
            )
            self._connections[connection_id] = connection

            if project_id not in self._project_connections:
                self._project_connections[project_id] = set()
            self._project_connections[project_id].add(connection_id)

            logger.info(
                "SSE connection added",
                extra={
                    "connection_id": connection_id,
                    "project_id": project_id,
                    "total_connections": len(self._connections),
                },
            )

            return connection

    async def remove_connection(self, connection_id: str) -> bool:
        """Remove an SSE connection."""
        async with self._lock:
            if connection_id not in self._connections:
                return False

            connection = self._connections.pop(connection_id)
            project_id = connection.project_id

            if project_id in self._project_connections:
                self._project_connections[project_id].discard(connection_id)
                if not self._project_connections[project_id]:
                    del self._project_connections[project_id]

            logger.info(
                "SSE connection removed",
                extra={
                    "connection_id": connection_id,
                    "project_id": project_id,
                    "total_connections": len(self._connections),
                },
            )

            return True

    async def get_connection(self, connection_id: str) -> SSEConnection | None:
        """Get a connection by ID."""
        async with self._lock:
            return self._connections.get(connection_id)

    async def get_project_connections(self, project_id: str) -> list[SSEConnection]:
        """Get all connections for a project."""
        async with self._lock:
            connection_ids = self._project_connections.get(project_id, set())
            return [
                self._connections[cid]
                for cid in connection_ids
                if cid in self._connections
            ]

    async def get_connection_count(self) -> int:
        """Get total number of active connections."""
        async with self._lock:
            return len(self._connections)

    async def get_project_connection_count(self, project_id: str) -> int:
        """Get number of connections for a project."""
        async with self._lock:
            return len(self._project_connections.get(project_id, set()))

    async def update_activity(self, connection_id: str) -> bool:
        """Update last activity timestamp for a connection."""
        async with self._lock:
            if connection_id in self._connections:
                self._connections[connection_id].last_activity = datetime.now()
                return True
            return False

    async def broadcast_to_project(
        self,
        project_id: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> int:
        """Broadcast a message to all connections for a project."""
        async with self._lock:
            connection_ids = self._project_connections.get(project_id, set())
            count = len(connection_ids)

            logger.info(
                "Broadcasting to project",
                extra={
                    "project_id": project_id,
                    "connection_count": count,
                    "message": message,
                },
            )

            return count

    async def cleanup_inactive_connections(
        self,
        max_age_seconds: int = 3600,
        callback: Callable[[str], Awaitable[None]] | None = None,
    ) -> int:
        """Clean up connections that have not had activity."""
        async with self._lock:
            now = datetime.now()
            to_remove = []

            for conn_id, connection in self._connections.items():
                age = now - connection.last_activity
                if age > timedelta(seconds=max_age_seconds):
                    to_remove.append(conn_id)

            for conn_id in to_remove:
                connection = self._connections.pop(conn_id)
                project_id = connection.project_id

                if project_id in self._project_connections:
                    self._project_connections[project_id].discard(conn_id)
                    if not self._project_connections[project_id]:
                        del self._project_connections[project_id]

                if callback:
                    await callback(conn_id)

            if to_remove:
                logger.info(
                    "Cleaned up inactive connections",
                    extra={"count": len(to_remove)},
                )

            return len(to_remove)


# Global singleton instance
_sse_manager: SSEConnectionManager | None = None


def get_sse_manager() -> SSEConnectionManager:
    """Get the global SSE connection manager instance."""
    global _sse_manager
    if _sse_manager is None:
        _sse_manager = SSEConnectionManager()
    return _sse_manager
