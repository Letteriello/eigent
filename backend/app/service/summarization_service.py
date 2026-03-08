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

"""Memory summarization service for condensing agent memories."""

import logging
from datetime import datetime, timedelta

from openai import AsyncOpenAI

from app.component.environment import env
from app.model.enums import MemoryType, SummaryLevel
from app.model.memory import MemoryCreate, MemoryResponse
from app.service.memory_service import MemoryService

logger = logging.getLogger("summarization_service")

# Default settings
DEFAULT_SUMMARY_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TOKENS = 1000
SESSION_SUMMARY_AGE_DAYS = 7
CONSOLIDATED_AGE_DAYS = 30

# Summary prompt template
SUMMARY_PROMPT_TEMPLATE = """You are an expert at condensing agent memories while preserving critical information.

Task: Summarize the following agent memories into a concise, structured format.

Requirements:
1. Preserve all factual information (entities, dates, actions)
2. Keep user preferences and stated goals
3. Note any important outcomes or decisions
4. Maintain temporal context (when relevant)
5. Identify patterns across multiple interactions

Format:
- Key Facts (bullet points)
- User Preferences (bullet points)
- Important Decisions/Outcomes (bullet points)
- Patterns/Observations (bullet points)

Memories to summarize:
{memory_content}

Summary:
"""

# Key facts extraction prompt
KEY_FACTS_PROMPT_TEMPLATE = """Extract key facts and entities from the following memories.

Categories to extract:
- person: Names of people mentioned
- organization: Companies, teams, projects
- technical: APIs, tools, functions, endpoints
- temporal: Dates, times, deadlines, schedules
- preferences: User preferences and settings

Return as a structured list of facts, one per line, prefixed with the category:
- [person] John mentioned he prefers morning meetings
- [technical] The API endpoint is /api/v1/memories
- [preference] User prefers dark mode

Memories:
{memory_content}

Key Facts:
"""


class SummarizationService:
    """Service for summarizing agent memories using LLM.

    Provides:
    - Session summarization: Summarize all memories from a single session
    - Consolidation: Merge multiple session summaries
    - Key facts extraction: Extract important entities and preferences

    Uses hierarchical approach:
    - Level 1: Raw conversations (kept for 7 days)
    - Level 2: Session summaries (kept for 30 days)
    - Level 3: Consolidated memory (kept long-term)
    - Level 4: Key facts (permanent)
    """

    def __init__(
        self,
        memory_service: MemoryService,
        model: str = DEFAULT_SUMMARY_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        """Initialize the summarization service.

        Args:
            memory_service: The memory service to use for storage
            model: LLM model to use for summarization
            max_tokens: Maximum tokens in generated summary
        """
        self.memory_service = memory_service
        self._model = model
        self._max_tokens = max_tokens
        self._client: AsyncOpenAI | None = None

    def _get_llm_client(self) -> AsyncOpenAI:
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            api_key = env("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for summarization")
            self._client = AsyncOpenAI(api_key=api_key)
        return self._client

    def _format_memories(self, memories: list[MemoryResponse]) -> str:
        """Format memories for inclusion in prompt."""
        lines = []
        for i, memory in enumerate(memories, 1):
            date_str = memory.created_at.strftime("%Y-%m-%d %H:%M")
            lines.append(f"[{i}] ({date_str}, {memory.memory_type.value}) {memory.content}")
        return "\n".join(lines)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (average 4 chars per token)."""
        return len(text) // 4

    async def _generate_summary(
        self, prompt: str, system_prompt: str | None = None
    ) -> str:
        """Generate summary using LLM.

        Args:
            prompt: User prompt with context
            system_prompt: Optional system prompt

        Returns:
            Generated summary text
        """
        client = self._get_llm_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=self._max_tokens,
                temperature=0.3,  # Lower temperature for more consistent summaries
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            raise

    async def summarize_session(self, session_id: str) -> MemoryResponse:
        """Generate summary for a single session.

        Args:
            session_id: The session ID to summarize

        Returns:
            Created summary memory

        Raises:
            ValueError: If session has no memories or already has a summary
        """
        # Get all memories for this session
        memories = await self.memory_service.list_memories(
            session_id=session_id,
            limit=1000,
        )

        # Filter out existing summaries
        original_memories = [m for m in memories if not m.is_summary]

        if not original_memories:
            raise ValueError(f"No memories found for session {session_id}")

        # Check if summary already exists
        existing_summaries = [
            m for m in memories
            if m.is_summary and m.summary_level == SummaryLevel.session.value
        ]
        if existing_summaries:
            logger.info(f"Session {session_id} already has a summary")
            return existing_summaries[0]

        # Build prompt
        formatted_memories = self._format_memories(original_memories)
        prompt = SUMMARY_PROMPT_TEMPLATE.format(memory_content=formatted_memories)

        # Generate summary
        summary_content = await self._generate_summary(prompt)

        # Create summary memory
        summary_memory = MemoryCreate(
            content=summary_content,
            memory_type=MemoryType.session_summary,
            metadata={
                "session_id": session_id,
                "source_memory_count": len(original_memories),
                "generated_at": datetime.utcnow().isoformat(),
            },
            agent_id=original_memories[0].agent_id,
            session_id=session_id,
        )

        # Add summary-specific fields via metadata (since MemoryCreate doesn't have them)
        result = await self.memory_service.create_memory(summary_memory)

        # Update with summary-specific fields
        await self.memory_service.update_memory(
            result.id,
            MemoryCreate(
                content=result.content,
                memory_type=result.memory_type,
                metadata={
                    **result.metadata,
                    "is_summary": True,
                    "summary_level": SummaryLevel.session.value,
                    "source_memory_ids": [m.id for m in original_memories],
                },
                agent_id=result.agent_id,
                session_id=result.session_id,
            ),
        )

        # Get the updated memory
        updated = await self.memory_service.get_memory(result.id)
        if not updated:
            raise ValueError("Failed to retrieve created summary")

        logger.info(
            f"Created session summary for {session_id} "
            f"from {len(original_memories)} memories"
        )
        return updated

    async def consolidate_summaries(self, days: int = 30) -> MemoryResponse | None:
        """Consolidate summaries older than specified days.

        Args:
            days: Age threshold in days for consolidation

        Returns:
            Created consolidated memory or None if no summaries to consolidate
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get all session summaries
        all_summaries = await self.memory_service.list_memories(
            memory_type=MemoryType.session_summary,
            limit=1000,
        )

        # Filter to old summaries that haven't been consolidated
        old_summaries = [
            s for s in all_summaries
            if s.created_at < cutoff_date
            and s.metadata.get("consolidated", False) is not True
        ]

        if len(old_summaries) < 2:
            logger.info("Not enough old summaries to consolidate")
            return None

        # Also include any existing consolidated summaries in the cutoff period
        consolidated = await self.memory_service.list_memories(
            memory_type=MemoryType.consolidated,
            limit=100,
        )
        recent_consolidated = [
            c for c in consolidated if c.created_at >= cutoff_date
        ]

        # Combine all summaries to consolidate
        to_consolidate = old_summaries + recent_consolidated
        source_ids = [s.id for s in to_consolidate]

        # Build prompt with all summaries
        formatted_summaries = self._format_memories(to_consolidate)
        prompt = f"""Consolidate the following session summaries into a single coherent summary.

Focus on:
1. Merging redundant information
2. Identifying cross-session patterns
3. Preserving unique insights from each session
4. Maintaining chronological context

Session Summaries:
{formatted_summaries}

Consolidated Summary:
"""

        consolidated_content = await self._generate_summary(
            prompt,
            system_prompt="You are an expert at merging and synthesizing multiple summaries "
            "while preserving all unique information and insights.",
        )

        # Create consolidated memory
        agent_ids = set(s.agent_id for s in to_consolidate if s.agent_id)
        consolidated_memory = MemoryCreate(
            content=consolidated_content,
            memory_type=MemoryType.consolidated,
            metadata={
                "source_memory_count": len(to_consolidate),
                "source_memory_ids": source_ids,
                "generated_at": datetime.utcnow().isoformat(),
                "consolidation_period_days": days,
            },
            agent_id=list(agent_ids)[0] if agent_ids else None,
        )

        result = await self.memory_service.create_memory(consolidated_memory)

        # Update with summary-specific fields
        await self.memory_service.update_memory(
            result.id,
            MemoryCreate(
                content=result.content,
                memory_type=result.memory_type,
                metadata={
                    **result.metadata,
                    "is_summary": True,
                    "summary_level": SummaryLevel.consolidated.value,
                    "source_memory_ids": source_ids,
                },
                agent_id=result.agent_id,
            ),
        )

        # Mark old summaries as consolidated
        for summary in old_summaries:
            await self.memory_service.update_memory(
                summary.id,
                MemoryCreate(
                    content=summary.content,
                    memory_type=summary.memory_type,
                    metadata={
                        **summary.metadata,
                        "consolidated": True,
                        "consolidated_into": result.id,
                    },
                    agent_id=summary.agent_id,
                    session_id=summary.session_id,
                ),
            )

        updated = await self.memory_service.get_memory(result.id)
        logger.info(
            f"Created consolidated summary from {len(to_consolidate)} session summaries"
        )
        return updated

    async def extract_key_facts(self, memories: list[MemoryResponse]) -> list[str]:
        """Extract key facts from memories.

        Args:
            memories: List of memories to extract facts from

        Returns:
            List of extracted key facts as strings
        """
        if not memories:
            return []

        # Group by memory type for better extraction
        by_type: dict[MemoryType, list[MemoryResponse]] = {}
        for memory in memories:
            if memory.memory_type not in by_type:
                by_type[memory.memory_type] = []
            by_type[memory.memory_type].append(memory)

        # Build prompt with categorized memories
        formatted = self._format_memories(memories)
        prompt = KEY_FACTS_PROMPT_TEMPLATE.format(memory_content=formatted)

        try:
            facts_text = await self._generate_summary(
                prompt,
                system_prompt="Extract factual information precisely. "
                "Each fact should be concise and self-contained.",
            )

            # Parse facts from response (one per line, optionally prefixed)
            facts = []
            for line in facts_text.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("*")):
                    # Remove bullet point
                    fact = line.lstrip("-* ").strip()
                    if fact and len(fact) > 10:  # Filter out very short lines
                        facts.append(fact)

            return facts

        except Exception as e:
            logger.error(f"Key facts extraction failed: {e}")
            # Fallback: return first 10 non-summary memories as "facts"
            return [m.content for m in memories[:10] if not m.is_summary]

    async def create_key_facts_memory(
        self,
        agent_id: str | None = None,
        days: int = 90,
    ) -> MemoryResponse | None:
        """Create a key facts memory from recent memories.

        Args:
            agent_id: Optional agent ID to filter by
            days: Age threshold in days

        Returns:
            Created key facts memory or None if no facts extracted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get all non-summary memories
        all_memories = await self.memory_service.list_memories(
            agent_id=agent_id,
            limit=1000,
        )

        # Filter to original memories older than cutoff
        old_memories = [
            m for m in all_memories
            if not m.is_summary and m.created_at < cutoff_date
        ]

        if not old_memories:
            logger.info("No memories old enough for key facts extraction")
            return None

        # Extract key facts
        key_facts = await self.extract_key_facts(old_memories)

        if not key_facts:
            return None

        facts_content = "Key Facts and Entities:\n\n" + "\n".join(
            f"- {fact}" for fact in key_facts
        )

        # Create key facts memory
        key_facts_memory = MemoryCreate(
            content=facts_content,
            memory_type=MemoryType.key_facts,
            metadata={
                "source_memory_count": len(old_memories),
                "source_memory_ids": [m.id for m in old_memories],
                "generated_at": datetime.utcnow().isoformat(),
                "facts_count": len(key_facts),
            },
            agent_id=agent_id,
        )

        result = await self.memory_service.create_memory(key_facts_memory)

        # Update with summary-specific fields
        await self.memory_service.update_memory(
            result.id,
            MemoryCreate(
                content=result.content,
                memory_type=result.memory_type,
                metadata={
                    **result.metadata,
                    "is_summary": True,
                    "summary_level": SummaryLevel.key_facts.value,
                    "source_memory_ids": [m.id for m in old_memories],
                },
                agent_id=result.agent_id,
            ),
        )

        updated = await self.memory_service.get_memory(result.id)
        logger.info(
            f"Created key facts memory with {len(key_facts)} facts "
            f"from {len(old_memories)} memories"
        )
        return updated

    async def get_memories_for_session(
        self, session_id: str
    ) -> list[MemoryResponse]:
        """Get all non-summary memories for a session.

        Args:
            session_id: The session ID

        Returns:
            List of original memories (not summaries)
        """
        memories = await self.memory_service.list_memories(
            session_id=session_id,
            limit=1000,
        )
        return [m for m in memories if not m.is_summary]

    async def get_pending_summaries(
        self, age_days: int = SESSION_SUMMARY_AGE_DAYS
    ) -> list[str]:
        """Get session IDs that need summarization.

        Args:
            age_days: Age threshold in days

        Returns:
            List of session IDs pending summarization
        """
        cutoff_date = datetime.utcnow() - timedelta(days=age_days)

        # Get all memories
        all_memories = await self.memory_service.list_memories(limit=10000)

        # Group by session
        sessions_with_memories: dict[str, list[MemoryResponse]] = {}
        for memory in all_memories:
            if memory.session_id and not memory.is_summary:
                if memory.session_id not in sessions_with_memories:
                    sessions_with_memories[memory.session_id] = []
                sessions_with_memories[memory.session_id].append(memory)

        # Find sessions that need summarization
        pending = []
        for session_id, memories in sessions_with_memories.items():
            # Check if oldest memory is old enough
            oldest = min(m.created_at for m in memories)
            if oldest < cutoff_date:
                # Check if summary doesn't exist
                has_summary = any(
                    m.is_summary
                    and m.summary_level == SummaryLevel.session.value
                    for m in all_memories
                    if m.session_id == session_id
                )
                if not has_summary:
                    pending.append(session_id)

        return pending


# Global summarization service instance
_summarization_service: SummarizationService | None = None


def get_summarization_service(
    memory_service: MemoryService | None = None,
) -> SummarizationService:
    """Get the global summarization service instance.

    Args:
        memory_service: Optional memory service to use

    Returns:
        The summarization service instance
    """
    global _summarization_service
    if _summarization_service is None:
        if memory_service is None:
            memory_service = MemoryService()
        _summarization_service = SummarizationService(memory_service)
    return _summarization_service
