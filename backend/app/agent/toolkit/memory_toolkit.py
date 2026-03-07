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
from typing import Any

from camel.toolkits.function_tool import FunctionTool

from app.agent.toolkit.abstract_toolkit import AbstractToolkit
from app.model.enums import MemoryType
from app.model.memory import MemoryCreate, MemorySearchQuery
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

            # Format results
            formatted = []
            for i, memory in enumerate(results.memories, 1):
                formatted.append(
                    f"{i}. [{memory.memory_type.value}] {memory.content}"
                )

            return "\n\n".join(formatted)

        except Exception as e:
            logger.error(f"Failed to recall memories: {e}", exc_info=True)
            return f"Error recalling memories: {str(e)}"

    def get_tools(self) -> list[FunctionTool]:
        """Return the list of tools provided by this toolkit."""
        return [
            FunctionTool(self.remember_fact),
            FunctionTool(self.remember_preference),
            FunctionTool(self.remember_context),
            FunctionTool(self.learn),
            FunctionTool(self.recall),
        ]

    @classmethod
    def get_can_use_tools(cls, api_task_id: str) -> list[FunctionTool]:
        """Return tools that can be used for a specific task/chat."""
        toolkit = cls(api_task_id)
        return toolkit.get_tools()
