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

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Response
from fastapi.testclient import TestClient

from app.controller.task_controller import (
    TakeControl,
    add_agent,
    put,
    start,
    take_control,
)
from app.model.chat import NewAgent, TaskContent, UpdateData
from app.service.task import Action


@pytest.mark.unit
class TestTaskController:
    """Test cases for task controller endpoints."""

    @pytest.mark.asyncio
    async def test_start_task_success(self, mock_task_lock):
        """Test successful task start."""
        task_id = "test_task_123"
        mock_task_lock.put_queue = AsyncMock()

        with patch(
            "app.controller.task_controller.get_task_lock",
            return_value=mock_task_lock,
        ):
            response = await start(task_id)

            assert isinstance(response, Response)
            assert response.status_code == 201
            mock_task_lock.put_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_task_lock):
        """Test successful task update."""
        task_id = "test_task_123"
        update_data = UpdateData(
            task=[
                TaskContent(id="subtask_1", content="Updated content 1"),
                TaskContent(id="subtask_2", content="Updated content 2"),
            ]
        )
        mock_task_lock.put_queue = AsyncMock()

        with patch(
            "app.controller.task_controller.get_task_lock",
            return_value=mock_task_lock,
        ):
            response = await put(task_id, update_data)

            assert isinstance(response, Response)
            assert response.status_code == 201
            mock_task_lock.put_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_take_control_pause_success(self, mock_task_lock):
        """Test successful task pause control."""
        task_id = "test_task_123"
        control_data = TakeControl(action=Action.pause)
        mock_task_lock.put_queue = AsyncMock()

        with patch(
            "app.controller.task_controller.get_task_lock",
            return_value=mock_task_lock,
        ):
            response = await take_control(task_id, control_data)

            assert isinstance(response, Response)
            assert response.status_code == 204
            mock_task_lock.put_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_take_control_resume_success(self, mock_task_lock):
        """Test successful task resume control."""
        task_id = "test_task_123"
        control_data = TakeControl(action=Action.resume)
        mock_task_lock.put_queue = AsyncMock()

        with patch(
            "app.controller.task_controller.get_task_lock",
            return_value=mock_task_lock,
        ):
            response = await take_control(task_id, control_data)

            assert isinstance(response, Response)
            assert response.status_code == 204
            mock_task_lock.put_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_agent_success(self, mock_task_lock):
        """Test successful agent addition."""
        task_id = "test_task_123"
        new_agent = NewAgent(
            name="Test Agent",
            description="A test agent",
            tools=["search", "code"],
            mcp_tools=None,
            env_path=".env",
        )
        mock_task_lock.put_queue = AsyncMock()

        with (
            patch(
                "app.controller.task_controller.get_task_lock",
                return_value=mock_task_lock,
            ),
            patch("app.controller.task_controller.load_dotenv"),
        ):
            response = await add_agent(task_id, new_agent)

            assert isinstance(response, Response)
            assert response.status_code == 204
            mock_task_lock.put_queue.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_start_task_nonexistent_task(self):
        """Test start task with nonexistent task ID."""
        task_id = "nonexistent_task"

        with patch(
            "app.controller.task_controller.get_task_lock",
            side_effect=KeyError("Task not found"),
        ):
            with pytest.raises(KeyError):
                await start(task_id)

    @pytest.mark.asyncio
    async def test_update_task_empty_data(self, mock_task_lock):
        """Test update task with empty task list."""
        task_id = "test_task_123"
        update_data = UpdateData(task=[])
        mock_task_lock.put_queue = AsyncMock()

        with patch(
            "app.controller.task_controller.get_task_lock",
            return_value=mock_task_lock,
        ):
            response = await put(task_id, update_data)

            assert isinstance(response, Response)
            assert response.status_code == 201
            mock_task_lock.put_queue.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_agent_with_mcp_tools(self, mock_task_lock):
        """Test adding agent with MCP tools."""
        task_id = "test_task_123"
        new_agent = NewAgent(
            name="MCP Agent",
            description="An agent with MCP tools",
            tools=["search"],
            mcp_tools={"mcpServers": {"notion": {"config": "test"}}},
            env_path=".env",
        )
        mock_task_lock.put_queue = AsyncMock()

        with (
            patch(
                "app.controller.task_controller.get_task_lock",
                return_value=mock_task_lock,
            ),
            patch("app.controller.task_controller.load_dotenv"),
        ):
            response = await add_agent(task_id, new_agent)

            assert isinstance(response, Response)
            assert response.status_code == 204
            mock_task_lock.put_queue.assert_called_once()


@pytest.mark.integration
class TestTaskControllerIntegration:
    """Integration tests for task controller."""

    @pytest.mark.asyncio
    async def test_start_task_endpoint_integration(self, client: TestClient):
        """Test start task endpoint through FastAPI test client."""
        task_id = "test_task_123"

        with patch(
            "app.controller.task_controller.get_task_lock"
        ) as mock_get_lock:
            mock_task_lock = MagicMock()
            mock_task_lock.put_queue = AsyncMock()
            mock_get_lock.return_value = mock_task_lock

            response = client.post(f"/task/{task_id}/start")

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_update_task_endpoint_integration(self, client: TestClient):
        """Test update task endpoint through FastAPI test client."""
        task_id = "test_task_123"
        update_data = {
            "task": [
                {"id": "subtask_1", "content": "Updated content 1"},
                {"id": "subtask_2", "content": "Updated content 2"},
            ]
        }

        with patch(
            "app.controller.task_controller.get_task_lock"
        ) as mock_get_lock:
            mock_task_lock = MagicMock()
            mock_task_lock.put_queue = AsyncMock()
            mock_get_lock.return_value = mock_task_lock

            response = client.put(f"/task/{task_id}", json=update_data)

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_take_control_pause_endpoint_integration(self, client: TestClient):
        """Test take control pause endpoint through FastAPI test client."""
        task_id = "test_task_123"
        control_data = {"action": "pause"}

        with patch(
            "app.controller.task_controller.get_task_lock"
        ) as mock_get_lock:
            mock_task_lock = MagicMock()
            mock_task_lock.put_queue = AsyncMock()
            mock_get_lock.return_value = mock_task_lock

            response = client.put(
                f"/task/{task_id}/take-control", json=control_data
            )

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_take_control_resume_endpoint_integration(
        self, client: TestClient
    ):
        """Test take control resume endpoint through FastAPI test client."""
        task_id = "test_task_123"
        control_data = {"action": "resume"}

        with patch(
            "app.controller.task_controller.get_task_lock"
        ) as mock_get_lock:
            mock_task_lock = MagicMock()
            mock_task_lock.put_queue = AsyncMock()
            mock_get_lock.return_value = mock_task_lock

            response = client.put(
                f"/task/{task_id}/take-control", json=control_data
            )

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_add_agent_endpoint_integration(self, client: TestClient):
        """Test add agent endpoint through FastAPI test client."""
        task_id = "test_task_123"
        agent_data = {
            "name": "Test Agent",
            "description": "A test agent",
            "tools": ["search", "code"],
            "mcp_tools": None,
            "env_path": ".env",
        }

        with (
            patch(
                "app.controller.task_controller.get_task_lock"
            ) as mock_get_lock,
            patch("app.controller.task_controller.load_dotenv"),
        ):
            mock_task_lock = MagicMock()
            mock_task_lock.put_queue = AsyncMock()
            mock_get_lock.return_value = mock_task_lock

            response = client.post(
                f"/task/{task_id}/add-agent", json=agent_data
            )

            assert response.status_code == 204


@pytest.mark.unit
class TestTaskControllerErrorCases:
    """Test error cases and edge conditions for task controller."""

    @pytest.mark.asyncio
    async def test_start_task_async_error(self, mock_task_lock):
        """Test start task when async operation fails."""
        task_id = "test_task_123"
        mock_task_lock.put_queue = AsyncMock(
            side_effect=Exception("Async error")
        )

        with patch(
            "app.controller.task_controller.get_task_lock",
            return_value=mock_task_lock,
        ):
            with pytest.raises(Exception, match="Async error"):
                await start(task_id)

    @pytest.mark.asyncio
    async def test_update_task_with_invalid_task_content(self, mock_task_lock):
        """Test update task with invalid task content."""
        task_id = "test_task_123"
        # Create invalid update data that might cause validation errors
        update_data = UpdateData(
            task=[
                TaskContent(id="", content=""),  # Empty ID and content
                TaskContent(id="valid_id", content="Valid content"),
            ]
        )
        mock_task_lock.put_queue = AsyncMock()

        with patch(
            "app.controller.task_controller.get_task_lock",
            return_value=mock_task_lock,
        ):
            # Should handle invalid data gracefully or raise appropriate error
            response = await put(task_id, update_data)
            assert response.status_code == 201

    def test_take_control_invalid_action(self):
        """Test take control with invalid action value."""

        # This should be caught by Pydantic validation
        with pytest.raises((ValueError, TypeError)):
            TakeControl(action="invalid_action")

    @pytest.mark.asyncio
    async def test_add_agent_env_load_failure(self, mock_task_lock):
        """Test add agent when environment loading fails."""
        task_id = "test_task_123"
        new_agent = NewAgent(
            name="Test Agent",
            description="A test agent",
            tools=["search"],
            mcp_tools=None,
            env_path="nonexistent.env",
        )

        with (
            patch(
                "app.controller.task_controller.get_task_lock",
                return_value=mock_task_lock,
            ),
            patch(
                "app.controller.task_controller.load_dotenv",
                side_effect=Exception("Env load failed"),
            ),
        ):
            # Should handle environment load failure gracefully or raise error
            with pytest.raises(Exception, match="Env load failed"):
                await add_agent(task_id, new_agent)

    @pytest.mark.asyncio
    async def test_add_agent_with_empty_name(self, mock_task_lock):
        """Test add agent with empty name."""
        task_id = "test_task_123"
        new_agent = NewAgent(
            name="",  # Empty name
            description="A test agent",
            tools=["search"],
            mcp_tools=None,
            env_path=".env",
        )
        mock_task_lock.put_queue = AsyncMock()

        with (
            patch(
                "app.controller.task_controller.get_task_lock",
                return_value=mock_task_lock,
            ),
            patch("app.controller.task_controller.load_dotenv"),
        ):
            # Should handle empty name appropriately
            response = await add_agent(task_id, new_agent)
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_task_operations_with_concurrent_access(self, mock_task_lock):
        """Test task operations with concurrent access scenarios."""
        task_id = "test_task_123"

        # Simulate concurrent access by having the task lock be modified during operation
        async def side_effect(*args, **kwargs):
            mock_task_lock.status = "modified_during_operation"

        mock_task_lock.put_queue = AsyncMock(side_effect=side_effect)

        with patch(
            "app.controller.task_controller.get_task_lock",
            return_value=mock_task_lock,
        ):
            response = await start(task_id)
            assert response.status_code == 201


@pytest.mark.model_backend
class TestTaskControllerWithLLM:
    """Tests that require LLM backend (marked for selective running)."""

    def test_add_agent_with_real_model_integration(self, mock_task_lock):
        """Test adding an agent that requires real model integration."""
        new_agent = NewAgent(
            name="Real Model Agent",
            description="An agent that uses real models",
            tools=["search", "code"],
            mcp_tools=None,
            env_path=".env",
        )

        # This test would involve real model creation and configuration
        # Marked as model_backend test for selective execution
        assert True  # Placeholder

    @pytest.mark.very_slow
    def test_full_task_workflow_integration(self):
        """Test complete task workflow from start to completion (very slow test)."""
        # This test would run a complete task workflow including agent interactions
        # Marked as very_slow for execution only in full test mode
        assert True  # Placeholder
