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

"""Memory service for persistent agent memory storage with hybrid search."""

import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from camel.embeddings import OpenAIEmbedding
from camel.storages import QdrantStorage
from pydantic import UUID4

from app.component.environment import env
from app.model.enums import MemoryType
from app.model.memory import (
    MemoryCreate,
    MemoryResponse,
    MemorySearchQuery,
    MemorySearchResult,
    MemoryStats,
    MemoryUpdate,
)

logger = logging.getLogger("memory_service")

# Default paths and constants
DEFAULT_MEMORY_STORAGE_PATH = "~/.eigent/memory_storage"
DEFAULT_COLLECTION_NAME = "agent_memory"
EMBEDDING_DIM = 1536  # OpenAI text-embedding-ada-002 dimension


class MemoryService:
    """Service for managing persistent agent memories.

    Provides CRUD operations with hybrid search combining:
    - Vector search via Qdrant (semantic similarity)
    - BM25 keyword search (keyword matching)
    - Reciprocal Rank Fusion (RRF) for combining results
    """

    def __init__(
        self,
        storage_path: str | Path | None = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        """Initialize the memory service.

        Args:
            storage_path: Path for vector storage. Defaults to ~/.eigent/memory_storage
            collection_name: Name for the Qdrant collection
        """
        self._storage_path = (
            Path(storage_path)
            if storage_path
            else Path(os.path.expanduser(DEFAULT_MEMORY_STORAGE_PATH))
        )
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._collection_name = collection_name
        self._embedding_model = None
        self._storage = None
        self._memories: dict[str, dict[str, Any]] = {}

    def _get_embedding_model(self):
        """Lazily initialize the embedding model."""
        if self._embedding_model is None:
            api_key = env("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for memory embeddings")
            self._embedding_model = OpenAIEmbedding(api_key=api_key)
        return self._embedding_model

    def _get_storage(self):
        """Lazily initialize Qdrant storage."""
        if self._storage is None:
            self._storage = QdrantStorage(
                vector_dim=EMBEDDING_DIM,
                path=str(self._storage_path),
                collection_name=self._collection_name,
            )
        return self._storage

    def _generate_memory_id(self, content: str) -> str:
        """Generate a unique ID for a memory based on content."""
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:12]

    def _memory_to_response(self, memory_data: dict[str, Any]) -> MemoryResponse:
        """Convert internal memory dict to response model."""
        return MemoryResponse(
            id=memory_data["id"],
            content=memory_data["content"],
            memory_type=MemoryType(memory_data["memory_type"]),
            metadata=memory_data.get("metadata", {}),
            agent_id=memory_data.get("agent_id"),
            session_id=memory_data.get("session_id"),
            importance=memory_data.get("importance", 1.0),
            created_at=memory_data["created_at"],
            updated_at=memory_data["updated_at"],
        )

    async def create_memory(self, memory: MemoryCreate) -> MemoryResponse:
        """Create a new memory entry.

        Args:
            memory: Memory creation schema

        Returns:
            Created memory response
        """
        now = datetime.utcnow()
        memory_id = self._generate_memory_id(memory.content)

        memory_data = {
            "id": memory_id,
            "content": memory.content,
            "memory_type": memory.memory_type.value,
            "metadata": memory.metadata,
            "agent_id": memory.agent_id,
            "session_id": memory.session_id,
            "importance": memory.metadata.get("importance", 1.0),
            "created_at": now,
            "updated_at": now,
        }

        # Store in memory dict for BM25
        self._memories[memory_id] = memory_data

        # Store in Qdrant for vector search
        try:
            storage = self._get_storage()
            embedding_model = self._get_embedding_model()
            vector = embedding_model.embed(memory.content)

            storage.write(
                vectors={[memory_id]: vector},
                payloads=[
                    {
                        "id": memory_id,
                        "content": memory.content,
                        "memory_type": memory.memory_type.value,
                        "metadata": memory.metadata,
                        "agent_id": memory.agent_id,
                        "session_id": memory.session_id,
                        "importance": memory_data["importance"],
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                    }
                ],
            )
            logger.info(f"Created memory {memory_id} in Qdrant")
        except Exception as e:
            logger.warning(f"Failed to store memory in Qdrant: {e}")
            # Continue with in-memory storage

        logger.info(f"Created memory: {memory_id}")
        return self._memory_to_response(memory_data)

    async def get_memory(self, memory_id: str) -> MemoryResponse | None:
        """Get a memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory response or None if not found
        """
        memory_data = self._memories.get(memory_id)
        if memory_data:
            return self._memory_to_response(memory_data)

        # Try to get from Qdrant
        try:
            storage = self._get_storage()
            results = storage.query(
                query_filter={"id": memory_id},
                top_k=1,
            )
            if results and len(results) > 0:
                payload = results[0].get("payload", {})
                if payload:
                    memory_data = {
                        "id": payload.get("id", memory_id),
                        "content": payload.get("content", ""),
                        "memory_type": payload.get("memory_type", "fact"),
                        "metadata": payload.get("metadata", {}),
                        "agent_id": payload.get("agent_id"),
                        "session_id": payload.get("session_id"),
                        "importance": payload.get("importance", 1.0),
                        "created_at": datetime.fromisoformat(
                            payload.get("created_at", datetime.utcnow().isoformat())
                        ),
                        "updated_at": datetime.fromisoformat(
                            payload.get("updated_at", datetime.utcnow().isoformat())
                        ),
                    }
                    self._memories[memory_id] = memory_data
                    return self._memory_to_response(memory_data)
        except Exception as e:
            logger.warning(f"Failed to query Qdrant: {e}")

        return None

    async def update_memory(
        self, memory_id: str, update: MemoryUpdate
    ) -> MemoryResponse | None:
        """Update an existing memory.

        Args:
            memory_id: Memory identifier
            update: Update schema

        Returns:
            Updated memory response or None if not found
        """
        memory_data = self._memories.get(memory_id)
        if not memory_data:
            return await self.get_memory(memory_id)

        now = datetime.utcnow()

        # Apply updates
        if update.content is not None:
            memory_data["content"] = update.content
        if update.memory_type is not None:
            memory_data["memory_type"] = update.memory_type.value
        if update.metadata is not None:
            memory_data["metadata"] = update.metadata
        memory_data["updated_at"] = now

        self._memories[memory_id] = memory_data

        # Update in Qdrant
        try:
            storage = self._get_storage()
            embedding_model = self._get_embedding_model()
            vector = embedding_model.embed(memory_data["content"])

            storage.write(
                vectors={[memory_id]: vector},
                payloads=[
                    {
                        "id": memory_id,
                        "content": memory_data["content"],
                        "memory_type": memory_data["memory_type"],
                        "metadata": memory_data["metadata"],
                        "agent_id": memory_data.get("agent_id"),
                        "session_id": memory_data.get("session_id"),
                        "importance": memory_data.get("importance", 1.0),
                        "created_at": memory_data["created_at"].isoformat(),
                        "updated_at": now.isoformat(),
                    }
                ],
            )
        except Exception as e:
            logger.warning(f"Failed to update memory in Qdrant: {e}")

        logger.info(f"Updated memory: {memory_id}")
        return self._memory_to_response(memory_data)

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            True if deleted, False if not found
        """
        if memory_id in self._memories:
            del self._memories[memory_id]
            logger.info(f"Deleted memory: {memory_id}")
            return True

        # Try Qdrant deletion (Qdrant doesn't have direct delete by ID,
        # would need to implement via upsert with empty vector or collection management)
        logger.info(f"Memory not found for deletion: {memory_id}")
        return False

    async def list_memories(
        self,
        memory_type: MemoryType | None = None,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[MemoryResponse]:
        """List memories with optional filters.

        Args:
            memory_type: Filter by memory type
            agent_id: Filter by agent ID
            limit: Maximum number of results

        Returns:
            List of memory responses
        """
        results = []

        for memory_data in self._memories.values():
            if memory_type and memory_data["memory_type"] != memory_type.value:
                continue
            if agent_id and memory_data.get("agent_id") != agent_id:
                continue
            results.append(self._memory_to_response(memory_data))

            if len(results) >= limit:
                break

        # Sort by created_at descending (newest first)
        results.sort(key=lambda m: m.created_at, reverse=True)

        return results[:limit]

    async def search_memories(
        self, search_query: MemorySearchQuery
    ) -> MemorySearchResult:
        """Search memories using hybrid search (vector + BM25 with RRF).

        Args:
            search_query: Search query schema

        Returns:
            Search results with ranked memories
        """
        query = search_query.query
        top_k = search_query.top_k

        # Vector search results
        vector_results = await self._vector_search(query, top_k * 2)

        # BM25 search results (if available)
        bm25_results = await self._bm25_search(query, top_k * 2)

        # Combine with Reciprocal Rank Fusion
        combined = self._reciprocal_rank_fusion(
            vector_results, bm25_results, top_k
        )

        # Apply filters
        filtered = []
        for memory_id in combined:
            memory_data = self._memories.get(memory_id)
            if not memory_data:
                continue

            # Apply memory_type filter
            if (
                search_query.memory_type
                and memory_data["memory_type"] != search_query.memory_type.value
            ):
                continue

            # Apply agent_id filter
            if (
                search_query.agent_id
                and memory_data.get("agent_id") != search_query.agent_id
            ):
                continue

            # Apply similarity threshold
            similarity = combined[memory_id]
            if similarity < search_query.similarity_threshold:
                continue

            filtered.append(self._memory_to_response(memory_data))

        logger.info(
            f"Search for '{query}' returned {len(filtered)} results"
        )

        return MemorySearchResult(
            memories=filtered[:top_k],
            total=len(filtered),
            query=query,
        )

    async def _vector_search(
        self, query: str, top_k: int
    ) -> dict[str, float]:
        """Perform vector similarity search.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Dict mapping memory_id to similarity score
        """
        results = {}

        try:
            storage = self._get_storage()
            embedding_model = self._get_embedding_model()
            query_vector = embedding_model.embed(query)

            search_results = storage.query(
                query_vector=query_vector,
                top_k=top_k,
            )

            for i, result in enumerate(search_results):
                memory_id = result.get("id") or result.get("payload", {}).get("id")
                if memory_id:
                    # Use rank-based score (1 / (rank + 1))
                    score = 1.0 / (i + 1)
                    results[memory_id] = score

        except Exception as e:
            logger.warning(f"Vector search failed: {e}")

        return results

    async def _bm25_search(
        self, query: str, top_k: int
    ) -> dict[str, float]:
        """Perform BM25 keyword search.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Dict mapping memory_id to BM25 score
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.debug("BM25 not available, skipping keyword search")
            return {}

        if not self._memories:
            return {}

        # Tokenize all memory contents
        corpus = []
        memory_ids = []

        for memory_id, memory_data in self._memories.items():
            # Tokenize content
            tokens = memory_data["content"].lower().split()
            corpus.append(tokens)
            memory_ids.append(memory_id)

        if not corpus:
            return {}

        # Create BM25 index
        bm25 = BM25Okapi(corpus)

        # Query
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)

        # Return top results
        results = {}
        sorted_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )

        for i in sorted_indices[:top_k]:
            if scores[i] > 0:
                results[memory_ids[i]] = scores[i]

        return results

    def _reciprocal_rank_fusion(
        self,
        vector_results: dict[str, float],
        bm25_results: dict[str, float],
        top_k: int,
        k: float = 60.0,
    ) -> dict[str, float]:
        """Combine search results using Reciprocal Rank Fusion.

        Args:
            vector_results: Vector search results (memory_id -> score)
            bm25_results: BM25 search results (memory_id -> score)
            top_k: Number of results to return
            k: RRF parameter (higher = more weight to lower ranks)

        Returns:
            Combined and ranked results
        """
        rrf_scores: dict[str, float] = {}

        # Add all memory IDs from vector results
        for memory_id in vector_results:
            rank = list(vector_results.keys()).index(memory_id) + 1
            rrf_scores[memory_id] = rrf_scores.get(memory_id, 0) + 1.0 / (k + rank)

        # Add all memory IDs from BM25 results
        for memory_id in bm25_results:
            rank = list(bm25_results.keys()).index(memory_id) + 1
            rrf_scores[memory_id] = rrf_scores.get(memory_id, 0) + 1.0 / (k + rank)

        # Sort by RRF score and return top_k
        sorted_results = sorted(
            rrf_scores.items(), key=lambda x: x[1], reverse=True
        )

        return dict(sorted_results[:top_k])

    async def get_stats(self) -> MemoryStats:
        """Get memory statistics.

        Returns:
            Memory statistics
        """
        by_type: dict[str, int] = {}
        by_agent: dict[str, int] = {}

        for memory_data in self._memories.values():
            mem_type = memory_data["memory_type"]
            by_type[mem_type] = by_type.get(mem_type, 0) + 1

            agent_id = memory_data.get("agent_id")
            if agent_id:
                by_agent[agent_id] = by_agent.get(agent_id, 0) + 1

        return MemoryStats(
            total_memories=len(self._memories),
            by_type=by_type,
            by_agent=by_agent,
        )


# Global memory service instance
_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Get the global memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
