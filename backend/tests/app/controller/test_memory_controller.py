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

"""Tests for memory controller endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.controller.memory_controller import (
    create_memory,
    delete_memory,
    get_memory,
    list_memories,
    search_memories,
    update_memory,
)
from app.model.enums import MemoryScope, MemoryType
from app.model.memory import (
    MemoryContextRequest,
    MemoryCreate,
    MemoryResponse,
    MemorySearchQuery,
    MemoryUpdate,
)


@pytest.mark.unit
class TestMemoryController:
    """Test cases for memory controller endpoints."""

    @pytest.fixture
    def mock_memory_response(self):
        """Create a mock memory response."""
        return MemoryResponse(
            id="test123",
            content="Test memory content",
            memory_type=MemoryType.fact,
            scope=MemoryScope.project,
            project_id="project-1",
            metadata={},
            agent_id=None,
            session_id=None,
            importance=1.0,
            is_summary=False,
            summary_level=None,
            source_memory_ids=[],
            is_encrypted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    @pytest.fixture
    def mock_memory_create(self):
        """Create a mock memory create request."""
        return MemoryCreate(
            content="Test memory content",
            memory_type=MemoryType.fact,
            scope=MemoryScope.project,
            project_id="project-1",
            metadata={},
        )

    @pytest.mark.asyncio
    async def test_create_memory_global_scope(self, mock_memory_response):
        """Test creating a memory with global scope."""
        mock_memory_response.scope = MemoryScope.global_
        mock_memory_response.project_id = None

        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_memory = AsyncMock(
                return_value=mock_memory_response
            )
            mock_get_service.return_value = mock_service

            memory_create = MemoryCreate(
                content="My name is John",
                memory_type=MemoryType.preference,
                scope=MemoryScope.global_,
                project_id=None,
            )

            result = await create_memory(memory_create)

            assert result.id == "test123"
            assert result.scope == MemoryScope.global_
            mock_service.create_memory.assert_called_once_with(memory_create)

    @pytest.mark.asyncio
    async def test_create_memory_project_scope(self, mock_memory_response):
        """Test creating a memory with project scope."""
        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_memory = AsyncMock(
                return_value=mock_memory_response
            )
            mock_get_service.return_value = mock_service

            memory_create = MemoryCreate(
                content="This is a project-specific memory",
                memory_type=MemoryType.context,
                scope=MemoryScope.project,
                project_id="project-123",
            )

            result = await create_memory(memory_create)

            assert result.id == "test123"
            assert result.scope == MemoryScope.project
            assert result.project_id == "project-1"

    @pytest.mark.asyncio
    async def test_create_memory_agent_scope(self, mock_memory_response):
        """Test creating a memory with agent scope."""
        mock_memory_response.scope = MemoryScope.agent
        mock_memory_response.agent_id = "agent-1"

        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_memory = AsyncMock(
                return_value=mock_memory_response
            )
            mock_get_service.return_value = mock_service

            memory_create = MemoryCreate(
                content="Agent-specific task memory",
                memory_type=MemoryType.learned,
                scope=MemoryScope.agent,
                project_id="project-123",
                agent_id="agent-1",
            )

            result = await create_memory(memory_create)

            assert result.scope == MemoryScope.agent
            assert result.agent_id == "agent-1"

    @pytest.mark.asyncio
    async def test_get_memory_by_id(self, mock_memory_response):
        """Test retrieving a memory by ID."""
        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_memory = AsyncMock(
                return_value=mock_memory_response
            )
            mock_get_service.return_value = mock_service

            result = await get_memory("test123")

            assert result.id == "test123"
            mock_service.get_memory.assert_called_once_with("test123")

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self):
        """Test getting a non-existent memory."""
        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_memory = AsyncMock(return_value=None)
            mock_get_service.return_value = mock_service

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await get_memory("nonexistent")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_memories_with_scope_filter(self, mock_memory_response):
        """Test listing memories filtered by scope."""
        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.list_memories = AsyncMock(
                return_value=[mock_memory_response]
            )
            mock_get_service.return_value = mock_service

            result = await list_memories(scope=MemoryScope.global_, limit=50)

            assert len(result) == 1
            mock_service.list_memories.assert_called_once_with(
                scope=MemoryScope.global_,
                project_id=None,
                memory_type=None,
                agent_id=None,
                limit=50,
            )

    @pytest.mark.asyncio
    async def test_list_memories_with_project_filter(
        self, mock_memory_response
    ):
        """Test listing memories filtered by project."""
        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.list_memories = AsyncMock(
                return_value=[mock_memory_response]
            )
            mock_get_service.return_value = mock_service

            result = await list_memories(
                scope=MemoryScope.project, project_id="project-1", limit=20
            )

            assert len(result) == 1
            mock_service.list_memories.assert_called_once_with(
                scope=MemoryScope.project,
                project_id="project-1",
                memory_type=None,
                agent_id=None,
                limit=20,
            )

    @pytest.mark.asyncio
    async def test_update_memory(self, mock_memory_response):
        """Test updating an existing memory."""
        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.update_memory = AsyncMock(
                return_value=mock_memory_response
            )
            mock_get_service.return_value = mock_service

            update = MemoryUpdate(content="Updated content")
            result = await update_memory("test123", update)

            assert result.id == "test123"
            mock_service.update_memory.assert_called_once_with(
                "test123", update
            )

    @pytest.mark.asyncio
    async def test_delete_memory_success(self):
        """Test deleting a memory successfully."""
        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.delete_memory = AsyncMock(return_value=True)
            mock_get_service.return_value = mock_service

            from app.controller.memory_controller import DeleteResponse

            result = await delete_memory("test123")

            assert result.success is True
            mock_service.delete_memory.assert_called_once_with("test123")

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self):
        """Test deleting a non-existent memory."""
        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.delete_memory = AsyncMock(return_value=False)
            mock_get_service.return_value = mock_service

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await delete_memory("nonexistent")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_search_memories(self, mock_memory_response):
        """Test searching memories."""
        from app.model.memory import MemorySearchResult

        with patch(
            "app.controller.memory_controller.get_memory_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.search_memories = AsyncMock(
                return_value=MemorySearchResult(
                    memories=[mock_memory_response], total=1, query="test"
                )
            )
            mock_get_service.return_value = mock_service

            search_query = MemorySearchQuery(query="test", top_k=5)
            result = await search_memories(search_query)

            assert result.total == 1
            assert result.query == "test"
            mock_service.search_memories.assert_called_once_with(search_query)


@pytest.mark.unit
class TestMemoryClassifier:
    """Test cases for memory classifier component."""

    @pytest.fixture
    def classifier(self):
        """Get memory classifier instance."""
        from app.component.memory_classifier import get_memory_classifier

        return get_memory_classifier()

    def test_classify_global_preference(self, classifier):
        """Test classifying global preference content."""
        content = "My name is John and I prefer dark mode"

        scope, mem_type = classifier.classify(content)

        assert scope == MemoryScope.global_
        assert mem_type in [MemoryType.preference, MemoryType.fact]

    def test_classify_global_personal(self, classifier):
        """Test classifying global personal content."""
        content = "My birthday is December 25th"

        scope, mem_type = classifier.classify(content)

        assert scope == MemoryScope.global_

    def test_classify_project_context(self, classifier):
        """Test classifying project context content."""
        content = "This project uses React for the frontend"

        scope, mem_type = classifier.classify(content)

        assert scope in [MemoryScope.project, MemoryScope.global_]

    def test_classify_agent_task(self, classifier):
        """Test classifying agent-specific task content."""
        content = "Remember to check the logs when working on this task"

        scope, mem_type = classifier.classify(content)

        assert scope == MemoryScope.agent

    def test_should_save_memory_indicator(self, classifier):
        """Test detecting save indicators in content."""
        content_with_indicator = "Remember that I prefer using TypeScript"

        assert classifier.should_save_memory(content_with_indicator) is True

    def test_should_save_memory_no_indicator(self, classifier):
        """Test content without save indicators."""
        content_without_indicator = "What is the weather today?"

        assert (
            classifier.should_save_memory(content_without_indicator) is False
        )


@pytest.mark.unit
class TestMemoryModels:
    """Test cases for memory models."""

    def test_memory_create_with_all_fields(self):
        """Test MemoryCreate with all fields."""
        memory = MemoryCreate(
            content="Test content",
            memory_type=MemoryType.preference,
            scope=MemoryScope.global_,
            project_id=None,
            agent_id="agent-1",
            session_id="session-1",
            metadata={"key": "value"},
        )

        assert memory.content == "Test content"
        assert memory.scope == MemoryScope.global_
        assert memory.agent_id == "agent-1"

    def test_memory_create_default_scope(self):
        """Test MemoryCreate default scope is project."""
        memory = MemoryCreate(content="Test content")

        assert memory.scope == MemoryScope.project

    def test_memory_context_request(self):
        """Test MemoryContextRequest model."""
        request = MemoryContextRequest(
            project_id="project-123",
            agent_id="agent-1",
            include_global=True,
            include_project=True,
            include_agent=True,
            limit=30,
        )

        assert request.project_id == "project-123"
        assert request.include_global is True
        assert request.limit == 30

    def test_memory_context_request_defaults(self):
        """Test MemoryContextRequest default values."""
        request = MemoryContextRequest(project_id="project-123")

        assert request.include_global is True
        assert request.include_project is True
        assert request.include_agent is True
        assert request.limit == 50
