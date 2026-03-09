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

"""Memory toolkit for agents to store and retrieve persistent memories.

This toolkit provides agents with the ability to:
- Remember important facts about the user or task
- Store user preferences
- Recall context from previous sessions
- Learn from interactions
"""

import logging
import time
from typing import Any

from camel.toolkits.function_tool import FunctionTool

from app.agent.toolkit.abstract_toolkit import AbstractToolkit
from app.model.enums import MemoryType
from app.model.memory import MemoryCreate, MemorySearchQuery, MemoryUpdate
from app.service.memory_service import get_memory_service

logger = logging.getLogger("memory_toolkit")


class MemoryToolkit(AbstractToolkit):
    """Toolkit for persistent agent memory operations.

    Provides tools for agents to store and retrieve memories
    across conversations and sessions.
    """

    agent_name: str = "memory_agent"  # Generic agent for memory operations

    def __init__(self, api_task_id: str, agent_id: str | None = None):
        """Initialize the MemoryToolkit.

        Args:
            api_task_id: The task/chat session ID
            agent_id: Optional agent identifier for filtering memories
        """
        self.api_task_id = api_task_id
        self.agent_id = agent_id
        self._service = None

    def _get_service(self):
        """Get the memory service instance."""
        if self._service is None:
            self._service = get_memory_service()
        return self._service

    def _log_tool_call(self, tool_name: str, **kwargs):
        """Log structured tool call metrics."""
        logger.info(
            "tool_call",
            tool=tool_name,
            agent_id=self.agent_id,
            session_id=self.api_task_id,
            **kwargs,
        )

    def _log_tool_result(self, tool_name: str, latency_ms: float, **kwargs):
        """Log structured tool result metrics."""
        logger.info(
            "tool_result",
            tool=tool_name,
            latency_ms=round(latency_ms, 2),
            **kwargs,
        )

    def _log_tool_error(self, tool_name: str, latency_ms: float, error: str):
        """Log structured tool error metrics."""
        logger.error(
            "tool_error",
            tool=tool_name,
            latency_ms=round(latency_ms, 2),
            error=error,
        )

    async def remember_fact(
        self,
        fact: str,
        importance: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store an important fact in memory.

        Use this to remember factual information that should be
        available in future conversations.

        Args:
            fact: The factual information to remember
            importance: Importance score (0-1), higher = more important (default: 1.0)
            metadata: Optional additional metadata

        Returns:
            Confirmation message with memory ID

        Example:
            remember_fact(
                fact="User prefers to work in the morning",
                importance=0.8
            )
        """
        try:
            meta = metadata or {}
            meta["importance"] = importance

            memory = MemoryCreate(
                content=fact,
                memory_type=MemoryType.fact,
                metadata=meta,
                agent_id=self.agent_id,
                session_id=self.api_task_id,
            )

            result = await self._get_service().create_memory(memory)
            return f"Fact remembered (ID: {result.id}): {fact}"

        except Exception as e:
            logger.error(f"Failed to remember fact: {e}", exc_info=True)
            return f"Error remembering fact: {str(e)}"

    async def remember_preference(
        self,
        preference: str,
        context: str | None = None,
        importance: float = 0.9,
    ) -> str:
        """Store a user preference in memory.

        Use this to remember user preferences like coding style,
        communication preferences, or tool preferences.

        Args:
            preference: The preference to remember
            context: Optional context about when this preference applies
            importance: Importance score (0-1) (default: 0.9)

        Returns:
            Confirmation message with memory ID

        Example:
            remember_preference(
                preference="Use TypeScript strict mode",
                context="When writing backend code"
            )
        """
        try:
            meta = {"importance": importance}
            if context:
                meta["context"] = context

            memory = MemoryCreate(
                content=preference,
                memory_type=MemoryType.preference,
                metadata=meta,
                agent_id=self.agent_id,
                session_id=self.api_task_id,
            )

            result = await self._get_service().create_memory(memory)
            return f"Preference remembered (ID: {result.id}): {preference}"

        except Exception as e:
            logger.error(f"Failed to remember preference: {e}", exc_info=True)
            return f"Error remembering preference: {str(e)}"

    async def remember_context(
        self,
        context: str,
        project: str | None = None,
    ) -> str:
        """Store current working context.

        Use this to remember the current project, task context,
        or working directory information.

        Args:
            context: The context information to remember
            project: Optional project name

        Returns:
            Confirmation message with memory ID

        Example:
            remember_context(
                context="Working on authentication feature",
                project="my-app"
            )
        """
        try:
            meta = {}
            if project:
                meta["project"] = project

            memory = MemoryCreate(
                content=context,
                memory_type=MemoryType.context,
                metadata=meta,
                agent_id=self.agent_id,
                session_id=self.api_task_id,
            )

            result = await self._get_service().create_memory(memory)
            return f"Context remembered (ID: {result.id}): {context}"

        except Exception as e:
            logger.error(f"Failed to remember context: {e}", exc_info=True)
            return f"Error remembering context: {str(e)}"

    async def learn(
        self,
        knowledge: str,
        source: str | None = None,
    ) -> str:
        """Store learned knowledge from interactions.

        Use this to record important knowledge gained during
        the conversation or task execution.

        Args:
            knowledge: The knowledge or insight to remember
            source: Optional source of the knowledge

        Returns:
            Confirmation message with memory ID

        Example:
            learn(
                knowledge="The API requires Bearer token authentication",
                source="user explanation"
            )
        """
        try:
            meta = {}
            if source:
                meta["source"] = source

            memory = MemoryCreate(
                content=knowledge,
                memory_type=MemoryType.learned,
                metadata=meta,
                agent_id=self.agent_id,
                session_id=self.api_task_id,
            )

            result = await self._get_service().create_memory(memory)
            return f"Knowledge learned and stored (ID: {result.id}): {knowledge}"

        except Exception as e:
            logger.error(f"Failed to learn: {e}", exc_info=True)
            return f"Error storing learned knowledge: {str(e)}"

    async def recall(
        self,
        query: str,
        memory_type: str | None = None,
        top_k: int = 5,
    ) -> str:
        """Recall relevant memories based on a query.

        Use this to retrieve previously stored memories that are
        relevant to the current conversation or task.

        Args:
            query: The search query to find relevant memories
            memory_type: Optional filter by memory type
                (fact, preference, context, learned)
            top_k: Number of memories to retrieve (default: 5)

        Returns:
            Formatted list of relevant memories, or message if none found

        Example:
            recall(
                query="user preferences",
                memory_type="preference",
                top_k=3
            )
        """
        start_time = time.perf_counter()
        self._log_tool_call("recall", query=query[:50], memory_type=memory_type, top_k=top_k)

        try:
            mem_type = None
            if memory_type:
                try:
                    mem_type = MemoryType(memory_type)
                except ValueError:
                    return f"Invalid memory_type: {memory_type}. Must be one of: fact, preference, context, learned"

            search_query = MemorySearchQuery(
                query=query,
                memory_type=mem_type,
                agent_id=self.agent_id,
                top_k=top_k,
                similarity_threshold=0.3,
            )

            results = await self._get_service().search_memories(search_query)

            if not results.memories:
                return f"No memories found matching: {query}"

            # Auto-boost importance of recalled memories
            for memory in results.memories:
                current_importance = memory.metadata.get("importance", 1.0) if memory.metadata else 1.0
                new_importance = min(current_importance + 1, 10.0)  # Max 10

                # Only update if importance changed significantly
                if new_importance > current_importance:
                    try:
                        await self._get_service().update_memory(
                            memory.id,
                            MemoryUpdate(metadata={"importance": new_importance}),
                        )
                        logger.debug(f"Boosted importance of memory {memory.id} from {current_importance} to {new_importance}")
                    except Exception as e:
                        logger.warning(f"Failed to boost importance: {e}")

            # Format results
            formatted = []
            for i, memory in enumerate(results.memories, 1):
                formatted.append(
                    f"{i}. [{memory.memory_type.value}] {memory.content}"
                )

            result = "\n\n".join(formatted)
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_tool_result("recall", latency_ms, result_count=len(results.memories))
            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_tool_error("recall", latency_ms, str(e))
            return f"Error recalling memories: {str(e)}"

    async def list_memories(
        self,
        memory_type: str | None = None,
        project_id: str | None = None,
        access_level: str | None = None,
        limit: int = 50,
    ) -> str:
        """List stored memories with optional filters.

        Use this to see what memories have been stored. Useful for
        reviewing existing memories before creating new ones.

        Args:
            memory_type: Optional filter by memory type
                (fact, preference, context, learned)
            project_id: Optional filter by project ID
            access_level: Optional filter by access level (private, team, global)
            limit: Maximum number of memories to return (default: 50)

        Returns:
            Formatted list of memories with their details

        Example:
            list_memories(memory_type="preference", limit=10)
        """
        start_time = time.perf_counter()
        self._log_tool_call("list_memories", memory_type=memory_type, project_id=project_id, access_level=access_level, limit=limit)

        try:
            mem_type = None
            if memory_type:
                try:
                    mem_type = MemoryType(memory_type)
                except ValueError:
                    return f"Invalid memory_type: {memory_type}. Must be one of: fact, preference, context, learned"

            acc_level = None
            if access_level:
                try:
                    from app.model.enums import AccessLevel
                    acc_level = AccessLevel(access_level)
                except ValueError:
                    return f"Invalid access_level: {access_level}. Must be one of: private, team, global"

            memories = await self._get_service().list_memories(
                memory_type=mem_type,
                agent_id=self.agent_id,
                project_id=project_id,
                access_level=acc_level,
                limit=limit,
            )

            if not memories:
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._log_tool_result("list_memories", latency_ms, result_count=0)
                return "No memories found"

            # Format results
            formatted = []
            for memory in memories:
                importance = memory.metadata.get("importance", 1.0) if memory.metadata else 1.0
                formatted.append(
                    f"[{memory.memory_type.value}] (importance: {importance}) {memory.content[:100]}..."
                )

            result = "\n\n".join(formatted)
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_tool_result("list_memories", latency_ms, result_count=len(memories))
            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_tool_error("list_memories", latency_ms, str(e))
            return f"Error listing memories: {str(e)}"
            logger.error(f"Failed to list memories: {e}", exc_info=True)
            return f"Error listing memories: {str(e)}"

    async def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        importance: float | None = None,
    ) -> str:
        """Update an existing memory's content or importance.

        Use this to correct or update memory content, or to adjust
        the importance score of a memory.

        Args:
            memory_id: The ID of the memory to update
            content: New content for the memory
            importance: New importance score (0-10), higher = more important

        Returns:
            Confirmation message

        Example:
            update_memory(memory_id="abc123", importance=0.9)
        """
        start_time = time.perf_counter()
        self._log_tool_call("update_memory", memory_id=memory_id, has_content=content is not None, has_importance=importance is not None)

        try:
            # Get existing memory to verify ownership
            existing = await self._get_service().get_memory(memory_id)
            if not existing:
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._log_tool_result("update_memory", latency_ms, found=False)
                return f"Memory not found: {memory_id}"

            # Security check: verify ownership
            if existing.agent_id and existing.agent_id != self.agent_id:
                logger.warning(f"Unauthorized update attempt: {memory_id} by {self.agent_id}")
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._log_tool_error("update_memory", latency_ms, "Unauthorized")
                return "Error: Cannot update memory from another agent"

            # Build update - only allow content and importance
            update_data = {}
            if content is not None:
                update_data["content"] = content

            if importance is not None:
                # Clamp importance to valid range
                clamped_importance = max(0.0, min(10.0, importance))
                # Preserve existing metadata and update importance
                existing_meta = dict(existing.metadata) if existing.metadata else {}
                existing_meta["importance"] = clamped_importance
                update_data["metadata"] = existing_meta

            if not update_data:
                return "Error: Must provide content or importance"

            await self._get_service().update_memory(
                memory_id,
                MemoryUpdate(**update_data),
            )

            logger.info(f"Memory {memory_id} updated by agent {self.agent_id}")
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_tool_result("update_memory", latency_ms, success=True)
            return f"Memory {memory_id} updated successfully"

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_tool_error("update_memory", latency_ms, str(e))
            return f"Error updating memory: {str(e)}"

    async def delete_memory(self, memory_id: str) -> str:
        """Delete a memory by ID.

        Use this to remove a memory that is no longer needed.
        Note: This is a hard delete - the memory is permanently removed.

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            Confirmation message

        Example:
            delete_memory(memory_id="abc123")
        """
        start_time = time.perf_counter()
        self._log_tool_call("delete_memory", memory_id=memory_id)

        try:
            # Get existing memory to verify ownership
            existing = await self._get_service().get_memory(memory_id)
            if not existing:
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._log_tool_result("delete_memory", latency_ms, found=False)
                return f"Memory not found: {memory_id}"

            # Security check: verify ownership
            if existing.agent_id and existing.agent_id != self.agent_id:
                logger.warning(f"Unauthorized delete attempt: {memory_id} by {self.agent_id}")
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._log_tool_error("delete_memory", latency_ms, "Unauthorized")
                return "Error: Cannot delete memory from another agent"

            # Log before deletion for audit
            logger.info(f"Deleting memory {memory_id} by agent {self.agent_id}")

            result = await self._get_service().delete_memory(memory_id)

            latency_ms = (time.perf_counter() - start_time) * 1000
            if result:
                self._log_tool_result("delete_memory", latency_ms, deleted=True)
                return f"Memory {memory_id} deleted successfully"
            else:
                self._log_tool_result("delete_memory", latency_ms, deleted=False)
                return f"Failed to delete memory: {memory_id}"

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_tool_error("delete_memory", latency_ms, str(e))
            return f"Error deleting memory: {str(e)}"

    async def get_memory_stats(self) -> str:
        """Get statistics about stored memories.

        Use this to get an overview of how many memories exist,
        broken down by type and agent.

        Returns:
            Formatted statistics about stored memories

        Example:
            get_memory_stats()
        """
        start_time = time.perf_counter()
        self._log_tool_call("get_memory_stats")

        try:
            stats = await self._get_service().get_stats()

            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_tool_result("get_memory_stats", latency_ms, total_memories=stats.total_memories)

            lines = [
                f"Total memories: {stats.total_memories}",
                "By type:",
            ]

            for mem_type, count in stats.by_type.items():
                lines.append(f"  - {mem_type}: {count}")

            if stats.by_agent:
                lines.append("By agent:")
                for agent_id, count in stats.by_agent.items():
                    lines.append(f"  - {agent_id}: {count}")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Failed to get stats: {e}", exc_info=True)
            return f"Error getting stats: {str(e)}"

    def get_tools(self) -> list[FunctionTool]:
        """Return the list of tools provided by this toolkit."""
        return [
            # Memory creation (manual)
            FunctionTool(self.remember_fact),
            FunctionTool(self.remember_preference),
            FunctionTool(self.remember_context),
            FunctionTool(self.learn),
            # Memory retrieval
            FunctionTool(self.recall),
            FunctionTool(self.list_memories),
            FunctionTool(self.get_memory_stats),
            # Memory management (with security)
            FunctionTool(self.update_memory),
            FunctionTool(self.delete_memory),
        ]

    @classmethod
    def get_can_use_tools(cls, api_task_id: str) -> list[FunctionTool]:
        """Return tools that can be used for a specific task/chat."""
        toolkit = cls(api_task_id)
        return toolkit.get_tools()
