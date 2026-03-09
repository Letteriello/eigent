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

"""Summarization scheduler for automatic memory consolidation."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.model.enums import MemoryType

logger = logging.getLogger("summarization_scheduler")


@dataclass
class SummarizationConfig:
    """Configuration for summarization scheduler."""

    age_threshold_days: int = 7
    token_threshold: int = 4000
    auto_summarize: bool = True
    schedule_cron: str = "0 2 * * *"  # 2 AM daily
    consolidate_age_days: int = 30
    archive_age_days: int = 90
    max_summaries_per_run: int = 50


class SummarizationScheduler:
    """Scheduler for automatic memory summarization.

    Handles age-based and size-based triggers for:
    - Session summarization (7 days old)
    - Summary consolidation (30 days old)
    - Key facts extraction (90 days old)

    Can be run on startup, via API, or as a background task.
    """

    def __init__(
        self,
        summarization_service: Any | None = None,
        memory_service: Any | None = None,
        config: SummarizationConfig | None = None,
    ):
        """Initialize the summarization scheduler.

        Args:
            summarization_service: Service for generating summaries
            memory_service: Service for memory CRUD operations
            config: Scheduler configuration
        """
        self.service = summarization_service
        self.memory_service = memory_service
        self.config = config or SummarizationConfig()
        self._scheduler_task: asyncio.Task | None = None

    async def run_scheduled_summarization(self) -> dict[str, Any]:
        """Run all scheduled summarization tasks.

        Returns:
            Dict with results of each summarization task
        """
        results = {
            "sessions_summarized": 0,
            "summaries_consolidated": 0,
            "lifecycle_transitions": {"stale_marked": 0, "archived": 0, "deleted": 0},
            "errors": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            # Step 1: Lifecycle transitions (always run first)
            if self.memory_service:
                lifecycle_result = await self.memory_service.daily_lifecycle_cleanup(
                    stale_threshold_days=14,
                    retention_days=30,
                    archive_retention_days=60,
                )
                results["lifecycle_transitions"] = lifecycle_result
                logger.info(f"Lifecycle transitions: {lifecycle_result}")

            # Step 2: Summarize old sessions
            sessions_result = await self.summarize_old_sessions(
                age_days=self.config.age_threshold_days
            )
            results["sessions_summarized"] = sessions_result.get("count", 0)

            # Step 3: Consolidate old summaries
            consolidation_result = await self.consolidate_old_summaries(
                age_days=self.config.consolidate_age_days
            )
            results["summaries_consolidated"] = consolidation_result.get("count", 0)

            logger.info(
                f"Summarization complete: {results['sessions_summarized']} sessions, "
                f"{results['summaries_consolidated']} consolidated, "
                f"lifecycle: {results['lifecycle_transitions']}"
            )

        except Exception as e:
            logger.error(f"Error in scheduled summarization: {e}")
            results["errors"].append(str(e))

        return results

    async def summarize_old_sessions(self, age_days: int = 7) -> dict[str, Any]:
        """Summarize sessions older than the specified age.

        Args:
            age_days: Age threshold in days

        Returns:
            Dict with count of summarized sessions and details
        """
        if not self.memory_service:
            logger.warning("Memory service not configured, skipping session summarization")
            return {"count": 0, "sessions": []}

        result = {"count": 0, "sessions": []}
        cutoff_date = datetime.utcnow() - timedelta(days=age_days)

        try:
            # Get all memories to find sessions that need summarization
            all_memories = await self.memory_service.list_memories(limit=10000)

            # Group by session
            sessions: dict[str, list] = {}
            for memory in all_memories:
                if memory.session_id:
                    if memory.session_id not in sessions:
                        sessions[memory.session_id] = []
                    sessions[memory.session_id].append(memory)

            # Find sessions older than cutoff that don't have summaries
            for session_id, memories in sessions.items():
                if not memories:
                    continue

                # Check if oldest memory is past cutoff
                oldest = min(memories, key=lambda m: m.created_at)
                if oldest.created_at < cutoff_date:
                    # Check if already summarized
                    has_summary = any(
                        m.memory_type == MemoryType.session_summary
                        and m.metadata.get("session_id") == session_id
                        for m in all_memories
                    )

                    if not has_summary:
                        # Summarize this session
                        try:
                            if self.service:
                                await self.service.summarize_session(session_id)
                                result["count"] += 1
                                result["sessions"].append(session_id)

                                if result["count"] >= self.config.max_summaries_per_run:
                                    break
                        except Exception as e:
                            logger.error(f"Error summarizing session {session_id}: {e}")

            logger.info(f"Summarized {result['count']} sessions older than {age_days} days")

        except Exception as e:
            logger.error(f"Error in summarize_old_sessions: {e}")

        return result

    async def consolidate_old_summaries(
        self, age_days: int = 30
    ) -> dict[str, Any]:
        """Consolidate summaries older than the specified age.

        Args:
            age_days: Age threshold in days

        Returns:
            Dict with count of consolidated summaries
        """
        if not self.memory_service:
            logger.warning(
                "Memory service not configured, skipping consolidation"
            )
            return {"count": 0, "summaries": []}

        result = {"count": 0, "summaries": []}
        cutoff_date = datetime.utcnow() - timedelta(days=age_days)

        try:
            # Get all session summaries
            all_memories = await self.memory_service.list_memories(limit=10000)

            # Find session summaries older than cutoff
            old_summaries = [
                m for m in all_memories
                if m.memory_type == MemoryType.session_summary
                and m.created_at < cutoff_date
            ]

            if not old_summaries:
                logger.info("No old summaries to consolidate")
                return result

            # Group by agent_id for consolidation
            by_agent: dict[str, list] = {}
            for summary in old_summaries:
                agent_id = summary.agent_id or "default"
                if agent_id not in by_agent:
                    by_agent[agent_id] = []
                by_agent[agent_id].append(summary)

            # Consolidate each agent's summaries
            for agent_id, summaries in by_agent.items():
                try:
                    if self.service:
                        consolidated = await self.service.consolidate_summaries(
                            summaries
                        )
                        if consolidated:
                            result["count"] += 1
                            result["summaries"].append(consolidated.id)
                except Exception as e:
                    logger.error(f"Error consolidating summaries for {agent_id}: {e}")

            logger.info(f"Consolidated {result['count']} summary groups")

        except Exception as e:
            logger.error(f"Error in consolidate_old_summaries: {e}")

        return result

    async def check_size_threshold(self) -> dict[str, Any]:
        """Check if any sessions exceed the token threshold.

        Returns:
            Dict with sessions that need summarization due to size
        """
        if not self.memory_service:
            return {"exceeds_threshold": False, "sessions": []}

        result = {"exceeds_threshold": False, "sessions": [], "total_tokens": 0}

        try:
            all_memories = await self.memory_service.list_memories(limit=10000)

            # Group by session
            sessions: dict[str, list] = {}
            for memory in all_memories:
                if memory.session_id:
                    if memory.session_id not in sessions:
                        sessions[memory.session_id] = []
                    sessions[memory.session_id].append(memory)

            # Calculate token counts
            for session_id, memories in sessions.items():
                total_tokens = sum(
                    self._estimate_tokens(m.content) for m in memories
                )

                if total_tokens > self.config.token_threshold:
                    result["exceeds_threshold"] = True
                    result["sessions"].append({
                        "session_id": session_id,
                        "token_count": total_tokens,
                        "memory_count": len(memories)
                    })
                    result["total_tokens"] += total_tokens

        except Exception as e:
            logger.error(f"Error in check_size_threshold: {e}")

        return result

    async def summarize_by_size(self) -> dict[str, Any]:
        """Summarize sessions that exceed token threshold.

        Returns:
            Dict with count of summarized sessions
        """
        size_check = await self.check_size_threshold()

        if not size_check.get("exceeds_threshold"):
            return {"count": 0}

        result = {"count": 0}

        for session_info in size_check.get("sessions", []):
            session_id = session_info.get("session_id")
            if session_id and self.service:
                try:
                    await self.service.summarize_session(session_id)
                    result["count"] += 1
                except Exception as e:
                    logger.error(f"Error summarizing session {session_id}: {e}")

        return result

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Rough estimate: ~4 characters per token on average.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    async def start_background_scheduler(self) -> None:
        """Start the background scheduler task.

        Note: This is a simple implementation. For production,
        consider using a proper cron library like apscheduler.
        """
        if self._scheduler_task and not self._scheduler_task.done():
            logger.warning("Scheduler already running")
            return

        if not self.config.auto_summarize:
            logger.info("Auto-summarize disabled, not starting scheduler")
            return

        async def run_periodic():
            while True:
                try:
                    await asyncio.sleep(3600)  # Check every hour
                    await self.run_scheduled_summarization()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in background scheduler: {e}")

        self._scheduler_task = asyncio.create_task(run_periodic())
        logger.info("Background summarization scheduler started")

    async def stop_background_scheduler(self) -> None:
        """Stop the background scheduler task."""
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
            logger.info("Background summarization scheduler stopped")

    async def run_on_startup(self) -> dict[str, Any]:
        """Run summarization on application startup.

        Returns:
            Dict with results of startup summarization
        """
        logger.info("Running startup summarization")
        return await self.run_scheduled_summarization()


# Global scheduler instance
_summarization_scheduler: SummarizationScheduler | None = None


def get_summarization_scheduler(
    memory_service: Any | None = None,
    config: SummarizationConfig | None = None,
) -> SummarizationScheduler:
    """Get the global summarization scheduler instance.

    Args:
        memory_service: Optional memory service to use
        config: Optional configuration to use

    Returns:
        The global summarization scheduler
    """
    global _summarization_scheduler

    if _summarization_scheduler is None:
        _summarization_scheduler = SummarizationScheduler(
            memory_service=memory_service, config=config
        )
    elif memory_service is not None:
        _summarization_scheduler.memory_service = memory_service

    return _summarization_scheduler
