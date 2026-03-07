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

"""Memory context injection utilities for agent prompts.

This module provides utilities to automatically inject relevant memories
into agent prompts, enabling agents to have context from previous
conversations and learned information.
"""

import logging

from app.model.enums import MemoryType
from app.model.memory import MemorySearchQuery
from app.service.memory_service import get_memory_service

logger = logging.getLogger("memory_context")

# Default prompt template for memory context
DEFAULT_MEMORY_CONTEXT_TEMPLATE = """\
## Relevant Memory Context
The following memories may be relevant to this conversation:
{memories}

---
This context was automatically retrieved from your long-term memory.
"""

# Short template for tool output
SHORT_MEMORY_CONTEXT_TEMPLATE = """\
## Relevant Memories
{memories}
"""


async def inject_memory_context(
    query: str,
    template: str | None = None,
    memory_types: list[MemoryType] | None = None,
    agent_id: str | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
) -> str:
    """Inject relevant memories into a prompt or get context.

    This function searches for memories relevant to the given query
    and returns them formatted for injection into a prompt.

    Args:
        query: The query to search memories for
        template: Custom template for formatting (uses default if None)
        memory_types: Optional list of memory types to filter
        agent_id: Optional agent ID to filter memories
        top_k: Maximum number of memories to retrieve
        similarity_threshold: Minimum similarity score

    Returns:
        Formatted memory context string, or empty string if no memories found

    Example:
        context = await inject_memory_context(
            query="What does the user prefer for code reviews?",
            memory_types=[MemoryType.preference, MemoryType.fact],
            top_k=3
        )
        # Returns: "## Relevant Memory Context\\n\\n1. [preference] User prefers..."
    """
    try:
        service = get_memory_service()

        search_query = MemorySearchQuery(
            query=query,
            memory_type=None,  # We filter manually for multiple types
            agent_id=agent_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        results = await service.search_memories(search_query)

        if not results.memories:
            return ""

        # Filter by memory types if specified
        filtered_memories = results.memories
        if memory_types:
            type_values = [mt.value for mt in memory_types]
            filtered_memories = [
                m for m in results.memories if m.memory_type.value in type_values
            ]

        if not filtered_memories:
            return ""

        # Format memories
        formatted = []
        for i, memory in enumerate(filtered_memories, 1):
            mem_type = memory.memory_type.value
            content = memory.content
            formatted.append(f"{i}. [{mem_type}] {content}")

        memories_text = "\n\n".join(formatted)

        # Use template or default
        if template:
            return template.format(memories=memories_text)

        return DEFAULT_MEMORY_CONTEXT_TEMPLATE.format(memories=memories_text)

    except Exception as e:
        logger.error(f"Failed to inject memory context: {e}", exc_info=True)
        return ""


async def get_memory_context_for_task(
    task_query: str,
    task_id: str,
    include_preferences: bool = True,
    include_facts: bool = True,
    include_context: bool = False,
    include_learned: bool = True,
) -> str:
    """Get formatted memory context for a specific task.

    Convenience function that automatically includes relevant memory types
    for a task-based query.

    Args:
        task_query: The task or query to find relevant memories for
        task_id: The task/chat session ID
        include_preferences: Include user preferences
        include_facts: Include factual memories
        include_context: Include context memories
        include_learned: Include learned knowledge

    Returns:
        Formatted memory context string

    Example:
        context = await get_memory_context_for_task(
            task_query="Implement user authentication",
            task_id="chat-123",
            include_preferences=True,
            include_facts=True
        )
    """
    memory_types = []
    if include_preferences:
        memory_types.append(MemoryType.preference)
    if include_facts:
        memory_types.append(MemoryType.fact)
    if include_context:
        memory_types.append(MemoryType.context)
    if include_learned:
        memory_types.append(MemoryType.learned)

    return await inject_memory_context(
        query=task_query,
        memory_types=memory_types if memory_types else None,
        agent_id=None,  # Could be extended to filter by agent
        top_k=5,
        similarity_threshold=0.3,
    )


def format_memory_for_prompt(memory_content: str, memory_type: str) -> str:
    """Format a single memory for inclusion in a prompt.

    Args:
        memory_content: The memory text
        memory_type: The type of memory (fact, preference, context, learned)

    Returns:
        Formatted memory string with type indicator

    Example:
        formatted = format_memory_for_prompt(
            "User prefers dark mode",
            "preference"
        )
        # Returns: "[preference] User prefers dark mode"
    """
    return f"[{memory_type}] {memory_content}"


class MemoryContextInjector:
    """Helper class for injecting memory context into prompts.

    This class can be used to build up memory context across
    multiple interactions within a single session.

    Example:
        injector = MemoryContextInjector(chat_id="chat-123")
        await injector.add_context("user likes Python")
        await injector.add_context("project is a web app")
        prompt = await injector.get_injected_prompt(base_prompt)
    """

    def __init__(self, chat_id: str, agent_id: str | None = None):
        """Initialize the injector.

        Args:
            chat_id: The chat/session ID
            agent_id: Optional agent ID for filtering
        """
        self.chat_id = chat_id
        self.agent_id = agent_id
        self._added_memories: list[str] = []

    async def add_context(self, query: str, top_k: int = 3) -> int:
        """Add relevant memories to the context.

        Searches for memories relevant to the query and adds them
        to the internal context list.

        Args:
            query: Query to search memories for
            top_k: Number of memories to retrieve

        Returns:
            Number of memories added
        """
        try:
            service = get_memory_service()

            search_query = MemorySearchQuery(
                query=query,
                agent_id=self.agent_id,
                top_k=top_k,
                similarity_threshold=0.3,
            )

            results = await service.search_memories(search_query)

            count = 0
            for memory in results.memories:
                formatted = format_memory_for_prompt(
                    memory.content, memory.memory_type.value
                )
                if formatted not in self._added_memories:
                    self._added_memories.append(formatted)
                    count += 1

            return count

        except Exception as e:
            logger.error(f"Failed to add context: {e}", exc_info=True)
            return 0

    async def get_injected_prompt(
        self,
        base_prompt: str,
        max_memories: int = 10,
    ) -> str:
        """Get the prompt with memory context injected.

        Args:
            base_prompt: The original prompt
            max_memories: Maximum number of memories to include

        Returns:
            Prompt with memory context appended

        Example:
            injector = MemoryContextInjector("chat-123")
            # ... add contexts ...
            full_prompt = await injector.get_injected_prompt(
                "Help the user with their task"
            )
        """
        if not self._added_memories:
            return base_prompt

        memories_to_include = self._added_memories[:max_memories]
        memories_text = "\n\n".join(memories_to_include)

        context_section = SHORT_MEMORY_CONTEXT_TEMPLATE.format(
            memories=memories_text
        )

        return f"{base_prompt}\n\n{context_section}"

    def clear(self) -> None:
        """Clear all added memories."""
        self._added_memories.clear()

    @property
    def memory_count(self) -> int:
        """Get the number of memories in context."""
        return len(self._added_memories)
