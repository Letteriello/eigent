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
import warnings
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.model.enums import MemoryType
from app.model.memory import MemoryResponse, MemorySearchQuery
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


# ========= Priority Scoring Weights =========
DEFAULT_IMPORTANCE_WEIGHT = 0.4
DEFAULT_RECENCY_WEIGHT = 0.3
DEFAULT_RELEVANCE_WEIGHT = 0.3

# Default token budget (~10% of 20k context window)
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TOP_K = 5


class TruncationStrategy(Enum):
    """Strategies for truncating memories when budget is exceeded."""

    RECENCY = "recency"  # Keep latest memories
    IMPORTANCE = "importance"  # Keep highest importance
    RELEVANCE = "relevance"  # Keep most relevant
    COMPOSITE = "composite"  # Use priority score (default)


@dataclass
class MemoryContextSettings:
    """Configurable settings for memory context injection.

    Attributes:
        max_tokens: Maximum token budget for memories (default: 2000)
        top_k: Maximum number of memories (default: 5, for backward compat)
        similarity_threshold: Minimum similarity score (default: 0.35)
        priority_type: Truncation strategy (default: composite)
        importance_weight: Weight for importance in composite score
        recency_weight: Weight for recency in composite score
        relevance_weight: Weight for relevance in composite score
        enable_deduplication: Whether to deduplicate similar memories
        dedup_similarity: Similarity threshold for deduplication
    """

    max_tokens: int = DEFAULT_MAX_TOKENS
    top_k: int = DEFAULT_TOP_K
    similarity_threshold: float = 0.35
    priority_type: TruncationStrategy = TruncationStrategy.COMPOSITE
    importance_weight: float = DEFAULT_IMPORTANCE_WEIGHT
    recency_weight: float = DEFAULT_RECENCY_WEIGHT
    relevance_weight: float = DEFAULT_RELEVANCE_WEIGHT
    enable_deduplication: bool = True
    dedup_similarity: float = 0.9

    def __post_init__(self):
        """Validate settings after initialization."""
        if self.max_tokens < 100:
            warnings.warn(
                "max_tokens should be at least 100 for meaningful context",
                UserWarning,
                stacklevel=2,
            )
        if self.similarity_threshold < 0 or self.similarity_threshold > 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        total_weight = (
            self.importance_weight
            + self.recency_weight
            + self.relevance_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            warnings.warn(
                f"Weights sum to {total_weight}, should sum to 1.0",
                UserWarning,
                stacklevel=2,
            )


# ========= Priority Scoring Functions =========


def calculate_recency_score(created_at: datetime) -> float:
    """Calculate recency score with exponential decay (24-hour half-life).

    Args:
        created_at: Memory creation timestamp

    Returns:
        Score from 0.0 to 1.0 (1.0 = now)
    """
    hours_old = (datetime.utcnow() - created_at).total_seconds() / 3600
    return 1.0 / (1.0 + hours_old / 24)


def calculate_priority_score(
    memory: MemoryResponse,
    relevance_score: float,
    importance_weight: float = DEFAULT_IMPORTANCE_WEIGHT,
    recency_weight: float = DEFAULT_RECENCY_WEIGHT,
    relevance_weight_param: float = DEFAULT_RELEVANCE_WEIGHT,
) -> float:
    """Calculate composite priority score for a memory.

    Formula: priority_score = (importance * 0.4) + (recency * 0.3) + (relevance * 0.3)

    Args:
        memory: The memory to score
        relevance_score: Similarity score from search (0.0-1.0)
        importance_weight: Weight for importance component
        recency_weight: Weight for recency component
        relevance_weight_param: Weight for relevance component

    Returns:
        Composite priority score (0.0-1.0)
    """
    # Recency: exponential decay with 24-hour half-life
    recency = calculate_recency_score(memory.created_at)

    # Importance: from memory field (default 0.5 if not set)
    importance = memory.importance if memory.importance else 0.5

    return (
        importance * importance_weight
        + recency * recency_weight
        + relevance_score * relevance_weight_param
    )


# ========= Token Budget Management =========


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses rough approximation: ~4 characters per token.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    return len(text) // 4


def calculate_total_tokens(memories: list[MemoryResponse]) -> int:
    """Calculate total tokens for a list of memories.

    Args:
        memories: List of memories

    Returns:
        Total estimated tokens
    """
    return sum(estimate_tokens(m.content) for m in memories)


# ========= Truncation Strategies =========


def truncate_by_token_budget(
    memories: list[tuple[MemoryResponse, float]],
    max_tokens: int,
) -> list[tuple[MemoryResponse, float]]:
    """Truncate memories to fit token budget.

    Selects memories in order until budget is exhausted.

    Args:
        memories: List of (memory, score) tuples
        max_tokens: Maximum token budget

    Returns:
        Filtered list within budget
    """
    selected = []
    tokens_used = 0

    for memory, score in memories:
        memory_tokens = estimate_tokens(memory.content)
        if tokens_used + memory_tokens <= max_tokens:
            selected.append((memory, score))
            tokens_used += memory_tokens
        else:
            # Try to fit if it's the first memory and alone
            if not selected and memory_tokens <= max_tokens:
                selected.append((memory, score))
            break

    return selected


def sort_by_truncation_strategy(
    memories: list[tuple[MemoryResponse, float]],
    strategy: TruncationStrategy,
    importance_weight: float = DEFAULT_IMPORTANCE_WEIGHT,
    recency_weight: float = DEFAULT_RECENCY_WEIGHT,
    relevance_weight: float = DEFAULT_RELEVANCE_WEIGHT,
) -> list[tuple[MemoryResponse, float]]:
    """Sort memories by the specified truncation strategy.

    Args:
        memories: List of (memory, relevance_score) tuples
        strategy: Truncation strategy to apply
        importance_weight: Weight for importance component
        recency_weight: Weight for recency component
        relevance_weight: Weight for relevance component

    Returns:
        Sorted list of (memory, score) tuples
    """
    if strategy == TruncationStrategy.RECENCY:
        scored = [
            (m, calculate_recency_score(m.created_at))
            for m, _ in memories
        ]
    elif strategy == TruncationStrategy.IMPORTANCE:
        scored = [
            (m, m.importance if m.importance else 0.5)
            for m, _ in memories
        ]
    elif strategy == TruncationStrategy.RELEVANCE:
        scored = memories  # Already sorted by relevance from search
    else:  # COMPOSITE
        scored = [
            (m, calculate_priority_score(m, s, importance_weight, recency_weight, relevance_weight))
            for m, s in memories
        ]

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def apply_truncation(
    memories: list[tuple[MemoryResponse, float]],
    max_tokens: int,
    strategy: TruncationStrategy = TruncationStrategy.COMPOSITE,
    importance_weight: float = DEFAULT_IMPORTANCE_WEIGHT,
    recency_weight: float = DEFAULT_RECENCY_WEIGHT,
    relevance_weight: float = DEFAULT_RELEVANCE_WEIGHT,
) -> list[MemoryResponse]:
    """Apply truncation strategies to fit token budget.

    Args:
        memories: List of (memory, relevance_score) tuples
        max_tokens: Maximum token budget
        strategy: Truncation strategy to apply
        importance_weight: Weight for importance component
        recency_weight: Weight for recency component
        relevance_weight: Weight for relevance component

    Returns:
        List of memories within budget, sorted by priority
    """
    if not memories:
        return []

    # Sort by strategy
    sorted_memories = sort_by_truncation_strategy(
        memories, strategy, importance_weight, recency_weight, relevance_weight
    )

    # Truncate to token budget
    truncated = truncate_by_token_budget(sorted_memories, max_tokens)

    # Return just the memories
    return [m for m, _ in truncated]


# ========= Deduplication =========


def deduplicate_memories(
    memories: list[MemoryResponse],
    similarity_threshold: float = 0.9,
) -> list[MemoryResponse]:
    """Deduplicate similar memories.

    Uses simple content comparison - considers duplicates if
    first 100 characters match and lengths are similar.

    Args:
        memories: List of memories to deduplicate
        similarity_threshold: Threshold for considering as duplicate

    Returns:
        Deduplicated list of memories
    """
    if not memories:
        return []

    unique = [memories[0]]
    for memory in memories[1:]:
        is_duplicate = False
        for unique_mem in unique:
            # Simple length check
            length_diff = abs(len(memory.content) - len(unique_mem.content))
            if length_diff < 10:
                # Check first 100 chars
                if memory.content[:100] == unique_mem.content[:100]:
                    is_duplicate = True
                    break
        if not is_duplicate:
            unique.append(memory)

    return unique


# ========= Adaptive Threshold =========


def get_adaptive_threshold(memory_types: list[MemoryType] | None) -> float:
    """Get adaptive threshold based on memory types.

    Research recommends different thresholds per memory type:
    - Preferences: 0.2-0.3 (lower - should rarely be missed)
    - Facts: 0.3-0.4
    - Learned: 0.35-0.5
    - Context: 0.25-0.35 (broader context is useful)

    Args:
        memory_types: List of memory types to include

    Returns:
        Recommended similarity threshold
    """
    if not memory_types:
        return 0.35  # Default

    # Use lowest threshold if any type needs it
    if MemoryType.preference in memory_types:
        return 0.2  # Lower for preferences

    if MemoryType.context in memory_types:
        return 0.3  # Medium for context

    if MemoryType.learned in memory_types:
        return 0.4  # Higher for learned

    return 0.35  # Default for facts


async def inject_memory_context(
    query: str,
    template: str | None = None,
    memory_types: list[MemoryType] | None = None,
    agent_id: str | None = None,
    top_k: int = 5,
    similarity_threshold: float | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    priority_type: TruncationStrategy = TruncationStrategy.COMPOSITE,
    importance_weight: float = DEFAULT_IMPORTANCE_WEIGHT,
    recency_weight: float = DEFAULT_RECENCY_WEIGHT,
    relevance_weight: float = DEFAULT_RELEVANCE_WEIGHT,
    enable_deduplication: bool = True,
) -> str:
    """Inject relevant memories into a prompt or get context.

    This function searches for memories relevant to the given query
    and returns them formatted for injection into a prompt.

    Args:
        query: The query to search memories for
        template: Custom template for formatting (uses default if None)
        memory_types: Optional list of memory types to filter
        agent_id: Optional agent ID to filter memories
        top_k: Maximum number of memories to retrieve (for backward compatibility)
        similarity_threshold: Minimum similarity score (auto-adapted if None)
        max_tokens: Maximum token budget for memories (default: 2000)
        priority_type: Truncation strategy (default: composite)
        importance_weight: Weight for importance in composite score
        recency_weight: Weight for recency in composite score
        relevance_weight: Weight for relevance in composite score
        enable_deduplication: Whether to deduplicate similar memories

    Returns:
        Formatted memory context string, or empty string if no memories found

    Example:
        context = await inject_memory_context(
            query="What does the user prefer for code reviews?",
            memory_types=[MemoryType.preference, MemoryType.fact],
            top_k=3,
            max_tokens=1000
        )
        # Returns: "## Relevant Memory Context\\n\\n1. [preference] User prefers..."
    """
    try:
        service = get_memory_service()

        # Use adaptive threshold if not specified
        if similarity_threshold is None:
            similarity_threshold = get_adaptive_threshold(memory_types)

        # Use higher top_k for retrieval, then truncate by token budget
        search_top_k = max(top_k * 4, 20)

        search_query = MemorySearchQuery(
            query=query,
            memory_type=None,  # We filter manually for multiple types
            agent_id=agent_id,
            top_k=search_top_k,
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

        # Deduplicate if enabled
        if enable_deduplication:
            filtered_memories = deduplicate_memories(filtered_memories)

        # Create (memory, relevance_score) tuples for truncation
        # Use search rank as proxy for relevance score
        memory_scores: list[tuple[MemoryResponse, float]] = [
            (m, 1.0 / (i + 1)) for i, m in enumerate(filtered_memories)
        ]

        # Apply truncation strategies with token budget
        final_memories = apply_truncation(
            memory_scores,
            max_tokens,
            priority_type,
            importance_weight,
            recency_weight,
            relevance_weight,
        )

        # Apply top_k limit (backward compatibility)
        final_memories = final_memories[:top_k]

        if not final_memories:
            return ""

        # Format memories
        formatted = []
        for i, memory in enumerate(final_memories, 1):
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
    max_tokens: int = DEFAULT_MAX_TOKENS,
    priority_type: TruncationStrategy = TruncationStrategy.COMPOSITE,
) -> str:
    """Get formatted memory context for a specific task.

    Convenience function that automatically includes relevant memory types
    for a task-based query.

    Args:
        task_query: The task or query to find relevant memories for
        task_id: The task/chat session ID (for future agent_id filtering)
        include_preferences: Include user preferences
        include_facts: Include factual memories
        include_context: Include context memories
        include_learned: Include learned knowledge
        max_tokens: Maximum token budget for memories
        priority_type: Truncation strategy to use

    Returns:
        Formatted memory context string

    Example:
        context = await get_memory_context_for_task(
            task_query="Implement user authentication",
            task_id="chat-123",
            include_preferences=True,
            include_facts=True,
            max_tokens=1000
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
        max_tokens=max_tokens,
        priority_type=priority_type,
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
