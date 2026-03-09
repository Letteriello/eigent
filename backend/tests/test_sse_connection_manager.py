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

"""Tests for SSE Connection Manager."""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock

from app.service.sse_manager import (
    SSEConnection,
    SSEConnectionManager,
    get_sse_manager,
)


@pytest.fixture
def manager():
    """Create a fresh SSEConnectionManager for each test."""
    return SSEConnectionManager()


class TestSSEConnection:
    """Tests for SSEConnection dataclass."""

    def test_connection_creation(self):
        """Test basic connection creation."""
        conn = SSEConnection(
            connection_id="test-1",
            project_id="project-1",
            user_id="user-1",
        )
        assert conn.connection_id == "test-1"
        assert conn.project_id == "project-1"
        assert conn.user_id == "user-1"
        assert conn.is_active is True

    def test_connection_defaults(self):
        """Test connection default values."""
        conn = SSEConnection(
            connection_id="test-2",
            project_id="project-2",
            user_id=None,
        )
        assert conn.created_at is not None
        assert conn.last_activity is not None
        assert conn.is_active is True


class TestSSEConnectionManager:
    """Tests for SSEConnectionManager."""

    @pytest.mark.asyncio
    async def test_add_connection(self, manager):
        """Test adding a connection."""
        conn = await manager.add_connection(
            connection_id="conn-1",
            project_id="project-1",
            user_id="user-1",
        )
        assert conn.connection_id == "conn-1"
        assert conn.project_id == "project-1"
        assert await manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_remove_connection(self, manager):
        """Test removing a connection."""
        await manager.add_connection("conn-1", "project-1")
        result = await manager.remove_connection("conn-1")
        assert result is True
        assert await manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_connection(self, manager):
        """Test removing a non-existent connection."""
        result = await manager.remove_connection("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_connection(self, manager):
        """Test retrieving a connection."""
        await manager.add_connection("conn-1", "project-1", "user-1")
        conn = await manager.get_connection("conn-1")
        assert conn is not None
        assert conn.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_get_project_connections(self, manager):
        """Test getting all connections for a project."""
        await manager.add_connection("conn-1", "project-1")
        await manager.add_connection("conn-2", "project-1")
        await manager.add_connection("conn-3", "project-2")

        connections = await manager.get_project_connections("project-1")
        assert len(connections) == 2

    @pytest.mark.asyncio
    async def test_get_project_connection_count(self, manager):
        """Test getting connection count for a project."""
        await manager.add_connection("conn-1", "project-1")
        await manager.add_connection("conn-2", "project-1")
        await manager.add_connection("conn-3", "project-2")

        count = await manager.get_project_connection_count("project-1")
        assert count == 2

        count = await manager.get_project_connection_count("project-2")
        assert count == 1

    @pytest.mark.asyncio
    async def test_update_activity(self, manager):
        """Test updating connection activity."""
        await manager.add_connection("conn-1", "project-1")
        conn_before = await manager.get_connection("conn-1")
        last_activity_before = conn_before.last_activity

        import time
        time.sleep(0.01)

        await manager.update_activity("conn-1")
        conn_after = await manager.get_connection("conn-1")
        
        assert conn_after.last_activity >= last_activity_before

    @pytest.mark.asyncio
    async def test_broadcast_to_project(self, manager):
        """Test broadcasting to project connections."""
        await manager.add_connection("conn-1", "project-1")
        await manager.add_connection("conn-2", "project-1")

        count = await manager.broadcast_to_project(
            "project-1",
            "test_message",
            {"key": "value"},
        )
        assert count == 2

    @pytest.mark.asyncio
    async def test_cleanup_inactive_connections(self, manager):
        """Test cleaning up inactive connections."""
        conn = await manager.add_connection("conn-1", "project-1")
        # Set last_activity to the past
        conn.last_activity = conn.created_at - timedelta(hours=2)

        callback = AsyncMock()
        cleaned = await manager.cleanup_inactive_connections(
            max_age_seconds=3600,
            callback=callback,
        )
        assert cleaned == 1
        assert await manager.get_connection_count() == 0
        callback.assert_called_once_with("conn-1")

    @pytest.mark.asyncio
    async def test_cleanup_no_connections_to_remove(self, manager):
        """Test cleanup when no connections need removal."""
        await manager.add_connection("conn-1", "project-1")
        cleaned = await manager.cleanup_inactive_connections(max_age_seconds=3600)
        assert cleaned == 0
        assert await manager.get_connection_count() == 1


class TestGetSseManager:
    """Tests for get_sse_manager singleton."""

    def test_singleton_returns_same_instance(self):
        """Test that get_sse_manager returns the same instance."""
        manager1 = get_sse_manager()
        manager2 = get_sse_manager()
        assert manager1 is manager2
