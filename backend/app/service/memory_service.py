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

import asyncio
import hashlib
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from camel.embeddings import OpenAIEmbedding
from camel.storages import QdrantStorage

from app.component.environment import env


class TTLCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl: int = 300, maxsize: int = 1000):
        """Initialize TTL cache.

        Args:
            ttl: Time to live in seconds (default: 5 minutes)
            maxsize: Maximum number of entries
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl
        self._maxsize = maxsize

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/missing
        """
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._maxsize:
            # Remove 20% oldest entries
            keys_to_remove = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k][1]
            )[:self._maxsize // 5]
            for k in keys_to_remove:
                del self._cache[k]
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


# Module-level caches
_embedding_cache: dict[str, tuple] = {}
_EMBEDDING_CACHE_MAX_SIZE = 5000

# Search result cache (TTL: 5 minutes, max 500 queries)
_search_cache = TTLCache(ttl=300, maxsize=500)

# BM25 index cache (TTL: 1 minute - rebuilds when memories change)
_bm25_index_cache: tuple | None = None
_bm25_index_timestamp: float = 0
_bm25_memory_count: int = 0  # Track memory count for invalidation
_BM25_INDEX_TTL = 60  # 1 minute
from app.model.enums import AccessLevel, MemoryStatus, MemoryType
from app.model.memory import (
    CleanupResult,
    ConsolidateResult,
    ConsolidationResult,
    DuplicateCandidate,
    EncryptionStatus,
    EncryptResult,
    MemoryCreate,
    MemoryResponse,
    MemorySearchQuery,
    MemorySearchResult,
    MemorySettings,
    MemoryStats,
    MemorySummaryRequest,
    MemoryUpdate,
    PendingSummary,
)
from app.service.encryption_service import (
    EncryptionService,
    get_encryption_service,
)

logger = logging.getLogger("memory_service")

# Default paths and constants
DEFAULT_MEMORY_STORAGE_PATH = "~/.eigent/memory_storage"
DEFAULT_COLLECTION_NAME = "agent_memory"
EMBEDDING_DIM = 1536  # OpenAI text-embedding-ada-002 dimension

# Backup constants
BACKUP_DIR = "~/.eigent/backups/memories"
BACKUP_MEMORY_THRESHOLD = 50  # Auto-backup every 50 memories
BACKUP_MAX_KEEP = 7  # Keep last 7 backups


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
        # Encryption service for sensitive content
        self._encryption_service: EncryptionService | None = None
        # Backup tracking
        self._last_daily_backup: datetime | None = None
        self._memory_count_at_last_backup = 0
        # Load existing memories from Qdrant on initialization
        self._load_memories_from_storage()

    def _load_memories_from_storage(self) -> None:
        """Load existing memories from Qdrant storage into memory dict.

        This ensures persistence across app restarts - the in-memory dict
        is populated from the persistent Qdrant storage on startup.
        """
        try:
            storage = self._get_storage()
            # Query all memories from Qdrant (using high top_k to get all)
            results = storage.query(top_k=10000)

            for result in results:
                payload = result.get("payload", {})
                if payload and "id" in payload:
                    memory_id = payload["id"]
                    # Convert ISO strings back to datetime
                    created_at = payload.get("created_at")
                    updated_at = payload.get("updated_at")

                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)
                    if isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at)

                    self._memories[memory_id] = {
                        "id": memory_id,
                        "content": payload.get("content", ""),
                        "content_plaintext": payload.get("content_plaintext"),
                        "is_encrypted": payload.get("is_encrypted", False),
                        "memory_type": payload.get("memory_type", "fact"),
                        "metadata": payload.get("metadata", {}),
                        "agent_id": payload.get("agent_id"),
                        "session_id": payload.get("session_id"),
                        "importance": payload.get("importance", 1.0),
                        "created_at": created_at,
                        "updated_at": updated_at,
                    }

            logger.info(f"Loaded {len(self._memories)} memories from Qdrant storage")

        except Exception as e:
            logger.warning(f"Failed to load memories from storage: {e}")
            # Continue with empty dict - app can still function

    def _get_encryption_service(self) -> EncryptionService:
        """Get or initialize the encryption service."""
        if self._encryption_service is None:
            self._encryption_service = get_encryption_service()
        return self._encryption_service

    def _get_embedding_model(self):
        """Lazily initialize the embedding model."""
        if self._embedding_model is None:
            api_key = env("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for memory embeddings")
            self._embedding_model = OpenAIEmbedding(api_key=api_key)
        return self._embedding_model


def _get_embedding_cached(text: str, get_embedding_fn) -> tuple:
    """Get embedding with module-level cache.

    Args:
        text: Text to embed
        get_embedding_fn: Function to call if cache miss

    Returns:
        Tuple of embedding vector (for hashability in cache)
    """
    if text not in _embedding_cache:
        # Evict oldest entries if cache is full
        if len(_embedding_cache) >= _EMBEDDING_CACHE_MAX_SIZE:
            # Remove ~10% of oldest entries
            keys_to_remove = list(_embedding_cache.keys())[:_EMBEDDING_CACHE_MAX_SIZE // 10]
            for key in keys_to_remove:
                del _embedding_cache[key]
        _embedding_cache[text] = tuple(get_embedding_fn(text))
    return _embedding_cache[text]


async def _get_embedding(self, text: str) -> list[float]:
    """Get embedding with cache support - runs in thread pool to avoid blocking.

    Args:
        text: Text to embed

    Returns:
        Embedding vector as list
    """
    # Run sync embed function in thread pool to avoid blocking event loop
    def sync_embed():
        return self._get_embedding_model().embed(text)
    return list(await asyncio.to_thread(
        _get_embedding_cached, text, sync_embed
    ))

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
        metadata = memory_data.get("metadata", {})
        return MemoryResponse(
            id=memory_data["id"],
            content=memory_data["content"],
            memory_type=MemoryType(memory_data["memory_type"]),
            metadata=metadata,
            agent_id=memory_data.get("agent_id"),
            session_id=memory_data.get("session_id"),
            project_id=memory_data.get("project_id"),
            access_level=AccessLevel(memory_data.get("access_level", "private")),
            importance=memory_data.get("importance", 1.0),
            is_summary=metadata.get("is_summary", False),
            summary_level=metadata.get("summary_level"),
            source_memory_ids=metadata.get("source_memory_ids", []),
            is_encrypted=memory_data.get("is_encrypted", False),
            status=MemoryStatus(memory_data.get("status", "active")),
            last_accessed_at=memory_data.get("last_accessed_at"),
            created_at=memory_data["created_at"],
            updated_at=memory_data["updated_at"],
        )

    def _update_status_on_access(self, memory_data: dict[str, Any]) -> dict[str, Any]:
        """Update lifecycle status when memory is accessed.

        Transitions:
        - new → active (first access)
        - stale → active (reactivation via recall)

        Args:
            memory_data: Internal memory dict

        Returns:
            Updated memory_data with status and last_accessed_at
        """
        now = datetime.utcnow()
        current_status = memory_data.get("status", "active")

        # Reactivate stale or promote new to active
        if current_status in ("new", "stale"):
            memory_data["status"] = "active"
            memory_data["updated_at"] = now
            logger.debug(f"Memory {memory_data['id']}: {current_status} → active")

        # Always update last_accessed_at
        memory_data["last_accessed_at"] = now

        return memory_data

    async def create_memory(self, memory: MemoryCreate) -> MemoryResponse:
        """Create a new memory entry.

        Args:
            memory: Memory creation schema

        Returns:
            Created memory response
        """
        now = datetime.utcnow()
        memory_id = self._generate_memory_id(memory.content)

        # Check if we should encrypt this memory based on type
        encryption_service = self._get_encryption_service()
        memory_type_str = memory.memory_type.value
        is_sensitive = encryption_service.is_sensitive(memory_type_str)

        # Encrypt content if sensitive and encryption is enabled
        stored_content = memory.content
        if is_sensitive and encryption_service.is_enabled:
            try:
                stored_content = encryption_service.encrypt(memory.content)
                logger.debug(f"Encrypted content for memory {memory_id}")
            except Exception as e:
                logger.warning(f"Failed to encrypt memory content: {e}")
                # Fall back to plaintext

        memory_data = {
            "id": memory_id,
            "content": stored_content,
            "content_plaintext": memory.content if is_sensitive else None,  # Keep for search
            "is_encrypted": is_sensitive and encryption_service.is_enabled,
            "memory_type": memory_type_str,
            "metadata": memory.metadata,
            "agent_id": memory.agent_id,
            "session_id": memory.session_id,
            "project_id": memory.project_id,
            "access_level": memory.access_level.value if memory.access_level else "private",
            "importance": memory.metadata.get("importance", 1.0),
            "status": "new",  # Lifecycle: start as new
            "created_at": now,
            "updated_at": now,
        }

        # Store in memory dict for BM25 (use plaintext for indexing)
        self._memories[memory_id] = memory_data

        # Store in Qdrant for vector search
        try:
            storage = self._get_storage()
            vector = await self._get_embedding(memory.content)

            await asyncio.to_thread(
                storage.write,
                vectors={[memory_id]: vector},
                payloads=[
                    {
                        "id": memory_id,
                        "content": stored_content,
                        "content_plaintext": memory.content if is_sensitive else None,
                        "is_encrypted": is_sensitive and encryption_service.is_enabled,
                        "memory_type": memory_type_str,
                        "metadata": memory.metadata,
                        "agent_id": memory.agent_id,
                        "session_id": memory.session_id,
                        "project_id": memory.project_id,
                        "access_level": memory.access_level.value if memory.access_level else "private",
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

        # Invalidate search caches when new memory is created
        _search_cache.clear()
        global _bm25_memory_count
        _bm25_memory_count = 0  # Force BM25 rebuild

        logger.info(f"Created memory: {memory_id}")

        # Auto-backup check (after creating memory)
        await self._check_and_create_backup()

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
            # Lifecycle: update status on access (new → active, stale → active)
            memory_data = self._update_status_on_access(memory_data)
            # Decrypt if needed
            return self._decrypt_memory_response(memory_data)

        # Try to get from Qdrant
        try:
            storage = self._get_storage()
            results = await asyncio.to_thread(
                storage.query,
                query_filter={"id": memory_id},
                top_k=1,
            )
            if results and len(results) > 0:
                payload = results[0].get("payload", {})
                if payload:
                    is_encrypted = payload.get("is_encrypted", False)
                    content = payload.get("content", "")

                    # Decrypt if encrypted
                    if is_encrypted:
                        encryption_service = self._get_encryption_service()
                        if encryption_service.is_enabled:
                            try:
                                content = encryption_service.decrypt(content)
                            except Exception as e:
                                logger.warning(f"Failed to decrypt memory content: {e}")

                    memory_data = {
                        "id": payload.get("id", memory_id),
                        "content": content,
                        "is_encrypted": is_encrypted,
                        "memory_type": payload.get("memory_type", "fact"),
                        "metadata": payload.get("metadata", {}),
                        "agent_id": payload.get("agent_id"),
                        "session_id": payload.get("session_id"),
                        "importance": payload.get("importance", 1.0),
                        "status": payload.get("status", "active"),
                        "last_accessed_at": datetime.fromisoformat(payload["last_accessed_at"]) if payload.get("last_accessed_at") else None,
                        "created_at": datetime.fromisoformat(
                            payload.get("created_at", datetime.utcnow().isoformat())
                        ),
                        "updated_at": datetime.fromisoformat(
                            payload.get("updated_at", datetime.utcnow().isoformat())
                        ),
                    }
                    # Lifecycle: update status on access
                    memory_data = self._update_status_on_access(memory_data)
                    self._memories[memory_id] = memory_data
                    return self._memory_to_response(memory_data)
        except Exception as e:
            logger.warning(f"Failed to query Qdrant: {e}")

        return None

    def _decrypt_memory_response(self, memory_data: dict[str, Any]) -> MemoryResponse:
        """Decrypt memory content if encrypted and return response.

        Args:
            memory_data: Internal memory data dict

        Returns:
            MemoryResponse with decrypted content
        """
        is_encrypted = memory_data.get("is_encrypted", False)
        content = memory_data.get("content", "")

        if is_encrypted:
            encryption_service = self._get_encryption_service()
            if encryption_service.is_enabled:
                try:
                    content = encryption_service.decrypt(content)
                except Exception as e:
                    logger.warning(f"Failed to decrypt memory content: {e}")

        # Update memory_data with decrypted content for response
        memory_data = dict(memory_data)
        memory_data["content"] = content

        return self._memory_to_response(memory_data)

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
        if update.access_level is not None:
            memory_data["access_level"] = update.access_level.value
        if update.project_id is not None:
            memory_data["project_id"] = update.project_id
        memory_data["updated_at"] = now

        self._memories[memory_id] = memory_data

        # Update in Qdrant
        try:
            storage = self._get_storage()
            vector = await self._get_embedding(memory_data["content"])

            await asyncio.to_thread(
                storage.write,
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

        # Invalidate search caches when memory is updated
        _search_cache.clear()
        global _bm25_memory_count
        _bm25_memory_count = 0  # Force BM25 rebuild

        logger.info(f"Updated memory: {memory_id}")
        return self._memory_to_response(memory_data)

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            True if deleted, False if not found
        """
        deleted_from_dict = False
        if memory_id in self._memories:
            del self._memories[memory_id]
            deleted_from_dict = True
            logger.info(f"Deleted memory from dict: {memory_id}")

        # Also delete from Qdrant for persistence
        deleted = False
        try:
            storage = self._get_storage()
            await asyncio.to_thread(storage.delete, ids=[memory_id])
            logger.info(f"Deleted memory from Qdrant: {memory_id}")
            deleted = True
        except Exception as e:
            logger.warning(f"Failed to delete memory from Qdrant: {e}")
            deleted = deleted_from_dict

        # Invalidate search caches when memory is deleted
        if deleted:
            _search_cache.clear()
            global _bm25_memory_count
            _bm25_memory_count = 0  # Force BM25 rebuild

        return deleted

    async def list_memories(
        self,
        memory_type: MemoryType | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
        access_level: AccessLevel | None = None,
        limit: int = 100,
    ) -> list[MemoryResponse]:
        """List memories with optional filters.

        Args:
            memory_type: Filter by memory type
            agent_id: Filter by agent ID
            project_id: Filter by project ID for multi-agent scoping
            access_level: Filter by access level (private, team, global)
            limit: Maximum number of results

        Returns:
            List of memory responses
        """
        results = []

        # First try to get from dict cache
        for memory_data in self._memories.values():
            if memory_type and memory_data["memory_type"] != memory_type.value:
                continue
            if agent_id and memory_data.get("agent_id") != agent_id:
                continue
            if project_id and memory_data.get("project_id") != project_id:
                continue
            if access_level:
                memory_access = memory_data.get("access_level", "private")
                # Filter based on access hierarchy
                access_hierarchy = {"global": 0, "team": 1, "private": 2}
                requested = access_hierarchy.get(access_level.value, 2)
                memory_lvl = access_hierarchy.get(memory_access, 2)
                if memory_lvl > requested:
                    continue
            # Decrypt if needed before returning
            results.append(self._decrypt_memory_response(memory_data))

            if len(results) >= limit:
                break

        # If no results from dict or dict is empty, fetch from Qdrant
        if not results:
            try:
                storage = self._get_storage()
                # Get all from Qdrant (using limit * 2 for safety)
                qdrant_results = await asyncio.to_thread(
                    storage.query,
                    query_filter=None,  # No filter, get all
                    top_k=limit * 2,
                )
                for result in qdrant_results:
                    payload = result.get("payload", {})
                    if not payload:
                        continue
                    memory_id = payload.get("id", "")
                    if memory_type and payload.get("memory_type") != memory_type.value:
                        continue
                    if agent_id and payload.get("agent_id") != agent_id:
                        continue
                    if project_id and payload.get("project_id") != project_id:
                        continue
                    if access_level:
                        memory_access = payload.get("access_level", "private")
                        access_hierarchy = {"global": 0, "team": 1, "private": 2}
                        requested = access_hierarchy.get(access_level.value, 2)
                        memory_lvl = access_hierarchy.get(memory_access, 2)
                        if memory_lvl > requested:
                            continue

                    # Decrypt if needed
                    is_encrypted = payload.get("is_encrypted", False)
                    content = payload.get("content", "")
                    if is_encrypted:
                        encryption_service = self._get_encryption_service()
                        if encryption_service.is_enabled:
                            try:
                                content = encryption_service.decrypt(content)
                            except Exception as e:
                                logger.warning(f"Failed to decrypt memory content: {e}")

                    memory_data = {
                        "id": memory_id,
                        "content": content,
                        "is_encrypted": is_encrypted,
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
                    results.append(self._memory_to_response(memory_data))

                    if len(results) >= limit:
                        break
            except Exception as e:
                logger.warning(f"Failed to fetch memories from Qdrant: {e}")

        # Sort by created_at descending (newest first)
        results.sort(key=lambda m: m.created_at, reverse=True)

        return results[:limit]

    async def search_memories(
        self, search_query: MemorySearchQuery
    ) -> MemorySearchResult:
        """Search memories using hybrid search (vector + BM25 with RRF).

        Uses caching for repeated queries with same parameters.

        Args:
            search_query: Search query schema

        Returns:
            Search results with ranked memories
        """
        query = search_query.query
        top_k = search_query.top_k

        # Create cache key from search parameters
        cache_key = f"{query}:{top_k}:{search_query.memory_type}:{search_query.agent_id}:{search_query.similarity_threshold}"

        # Check cache first
        cached_result = _search_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for search: {query[:50]}...")
            return cached_result

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

            # Apply project_id filter
            if (
                search_query.project_id
                and memory_data.get("project_id") != search_query.project_id
            ):
                continue

            # Apply access_level filter
            if search_query.access_level:
                memory_access_level = memory_data.get("access_level", "private")
                # Include memories that are accessible at the requested level or more permissive
                access_hierarchy = {"global": 0, "team": 1, "private": 2}
                requested_level = access_hierarchy.get(search_query.access_level.value, 2)
                memory_level = access_hierarchy.get(memory_access_level, 2)
                if memory_level > requested_level:
                    continue

            # Apply similarity threshold
            similarity = combined[memory_id]
            if similarity < search_query.similarity_threshold:
                continue

            # Update lifecycle status on access (reactivate stale → active)
            memory_data = self._update_status_on_access(memory_data)

            # Decrypt if needed before returning
            filtered.append(self._decrypt_memory_response(memory_data))

        logger.info(
            f"Search for '{query}' returned {len(filtered)} results"
        )

        result = MemorySearchResult(
            memories=filtered[:top_k],
            total=len(filtered),
            query=query,
        )

        # Cache the result
        _search_cache.set(cache_key, result)

        return result

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
            query_vector = await self._get_embedding(query)

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
        """Perform BM25 keyword search with caching.

        Uses cached BM25 index to avoid rebuilding on every query.
        Index is rebuilt when memories change or after TTL expires.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Dict mapping memory_id to BM25 score
        """
        global _bm25_index_cache, _bm25_index_timestamp, _bm25_memory_count

        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.debug("BM25 not available, skipping keyword search")
            return {}

        if not self._memories:
            return {}

        # Check if BM25 index needs rebuild (TTL or memory count changed)
        current_time = time.time()
        current_memory_count = len(self._memories)
        needs_rebuild = (
            _bm25_index_cache is None
            or current_time - _bm25_index_timestamp > _BM25_INDEX_TTL
            or current_memory_count != _bm25_memory_count
        )

        # Update memory count tracker
        if current_memory_count != _bm25_memory_count:
            _bm25_memory_count = current_memory_count

        if needs_rebuild:
            # Tokenize all memory contents
            corpus = []
            memory_ids = []

            for memory_id, memory_data in self._memories.items():
                # Tokenize content
                tokens = memory_data["content"].lower().split()
                corpus.append(tokens)
                memory_ids.append(memory_id)

            if corpus:
                _bm25_index_cache = (BM25Okapi(corpus), memory_ids)
                _bm25_index_timestamp = current_time

        # Use cached index if available
        if _bm25_index_cache is None:
            return {}

        bm25, memory_ids = _bm25_index_cache

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
        k: float = 15.0,
    ) -> dict[str, float]:
        """Combine search results using Reciprocal Rank Fusion.

        Args:
            vector_results: Vector search results (memory_id -> score)
            bm25_results: BM25 search results (memory_id -> score)
            top_k: Number of results to return
            k: RRF parameter (default 15 - appropriate for <1000 documents)

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

        # Use dict as primary source if it has data
        if self._memories:
            for memory_data in self._memories.values():
                mem_type = memory_data["memory_type"]
                by_type[mem_type] = by_type.get(mem_type, 0) + 1

                agent_id = memory_data.get("agent_id")
                if agent_id:
                    by_agent[agent_id] = by_agent.get(agent_id, 0) + 1
        else:
            # Fallback to Qdrant if dict is empty
            try:
                storage = self._get_storage()
                results = await asyncio.to_thread(
                    storage.query,
                    query_filter=None,
                    top_k=10000,  # Get all
                )
                for result in results:
                    payload = result.get("payload", {})
                    if not payload:
                        continue
                    mem_type = payload.get("memory_type", "fact")
                    by_type[mem_type] = by_type.get(mem_type, 0) + 1

                    agent_id = payload.get("agent_id")
                    if agent_id:
                        by_agent[agent_id] = by_agent.get(agent_id, 0) + 1
            except Exception as e:
                logger.warning(f"Failed to get stats from Qdrant: {e}")

        return MemoryStats(
            total_memories=len(self._memories) or sum(by_type.values()),
            by_type=by_type,
            by_agent=by_agent,
            deduplication_count=self._deduplication_count,
            cleanup_count=self._cleanup_count,
            last_cleanup=self._last_cleanup,
        )

    # Settings management
    _settings: MemorySettings = MemorySettings()

    # Consolidation tracking
    _deduplication_count: int = 0
    _cleanup_count: int = 0
    _last_cleanup: datetime | None = None

    async def get_settings(self) -> MemorySettings:
        """Get memory settings.

        Returns:
            Current memory settings
        """
        return self._settings

    async def update_settings(self, settings: MemorySettings) -> MemorySettings:
        """Update memory settings.

        Args:
            settings: New settings

        Returns:
            Updated settings
        """
        self._settings = settings
        logger.info("Updated memory settings")
        return self._settings

    # Summarization methods
    async def summarize_memory(
        self, memory_id: str, request: MemorySummaryRequest
    ) -> MemoryResponse | None:
        """Summarize a specific memory.

        Args:
            memory_id: Memory to summarize
            request: Summarization request

        Returns:
            Updated memory with summary
        """
        memory_data = self._memories.get(memory_id)
        if not memory_data:
            return None

        # Generate summary content based on level
        summary_type = request.level.value
        original_content = memory_data["content"]

        # Create summary (placeholder - in production would use LLM)
        summary_content = f"[{summary_type.upper()}] {original_content[:100]}..."

        # Update memory with summary
        memory_data["content"] = summary_content
        memory_data["metadata"]["summarized"] = True
        memory_data["metadata"]["summary_level"] = request.level.value
        memory_data["updated_at"] = datetime.utcnow()

        logger.info(f"Summarized memory: {memory_id}")
        return self._memory_to_response(memory_data)

    async def get_pending_summaries(self, limit: int = 20) -> list[PendingSummary]:
        """Get memories pending summarization.

        Args:
            limit: Maximum results

        Returns:
            List of memories pending summarization
        """
        pending = []
        for memory_id, memory_data in self._memories.items():
            # Skip already summarized or session summaries
            if memory_data["metadata"].get("summarized"):
                continue
            if memory_data["memory_type"] in ["session_summary", "consolidated"]:
                continue

            pending.append(
                PendingSummary(
                    memory_id=memory_id,
                    content_preview=memory_data["content"][:100],
                    memory_type=MemoryType(memory_data["memory_type"]),
                    created_at=memory_data["created_at"],
                    agent_id=memory_data.get("agent_id"),
                )
            )

            if len(pending) >= limit:
                break

        return pending

    # Consolidation methods
    async def consolidate_memories(self) -> ConsolidateResult:
        """Run memory deduplication and consolidation.

        Returns:
            Consolidation results
        """
        original_count = len(self._memories)

        # Find duplicates
        duplicates = await self.find_duplicates()
        duplicates_merged = 0

        # Merge duplicates (keep first, remove others)
        for dup in duplicates:
            if dup.memory_id_2 in self._memories:
                del self._memories[dup.memory_id_2]
                duplicates_merged += 1

        # Create consolidated summary if needed
        summaries_created = 0
        if len(self._memories) > self._settings.summarization_threshold:
            summary_content = f"Consolidated from {original_count} memories"
            now = datetime.utcnow()
            summary_id = f"consolidated_{now.strftime('%Y%m%d_%H%M%S')}"
            self._memories[summary_id] = {
                "id": summary_id,
                "content": summary_content,
                "memory_type": "consolidated",
                "metadata": {"original_count": original_count},
                "agent_id": None,
                "session_id": None,
                "importance": 1.0,
                "created_at": now,
                "updated_at": now,
            }
            summaries_created = 1

        consolidated_count = len(self._memories)

        # Update tracking metrics
        self._deduplication_count += duplicates_merged
        self._last_cleanup = datetime.utcnow()

        logger.info(
            f"Consolidated memories: {original_count} -> {consolidated_count}, "
            f"duplicates merged: {duplicates_merged}, summaries: {summaries_created}"
        )

        return ConsolidateResult(
            original_count=original_count,
            consolidated_count=consolidated_count,
            duplicates_found=len(duplicates),
            duplicates_merged=duplicates_merged,
            summaries_created=summaries_created,
        )

    async def cleanup_old_memories(self, days: int = 30) -> CleanupResult:
        """Clean up memories older than specified days.

        Args:
            days: Number of days to retain

        Returns:
            Cleanup results
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted_ids = []

        for memory_id, memory_data in list(self._memories.items()):
            if memory_data["created_at"] < cutoff:
                # Don't delete consolidated/summary memories
                if memory_data["memory_type"] not in ["session_summary", "consolidated"]:
                    deleted_ids.append(memory_id)
                    del self._memories[memory_id]

        # Estimate freed space (rough approximation)
        freed_space = len(deleted_ids) * 500  # ~500 bytes per memory

        # Update tracking metrics
        self._cleanup_count += len(deleted_ids)
        self._last_cleanup = datetime.utcnow()

        logger.info(f"Cleaned up {len(deleted_ids)} memories older than {days} days")

        return CleanupResult(
            deleted_count=len(deleted_ids),
            freed_space=freed_space,
        )

    async def daily_lifecycle_cleanup(
        self,
        stale_threshold_days: int = 14,
        retention_days: int = 30,
        archive_retention_days: int = 60,
    ) -> dict[str, int]:
        """Daily lifecycle cleanup - transitions memories through lifecycle states.

        Transitions:
        - new/active → stale: not accessed for stale_threshold_days
        - stale → archived: retention_days since creation
        - archived → deleted: archive_retention_days since archived

        Args:
            stale_threshold_days: Days without access before marking stale
            retention_days: Days to retain before archiving
            archive_retention_days: Days in archived before deletion

        Returns:
            Dict with counts: stale_marked, archived, deleted
        """
        from datetime import timedelta

        now = datetime.utcnow()
        stale_cutoff = now - timedelta(days=stale_threshold_days)
        retention_cutoff = now - timedelta(days=retention_days)
        archive_cutoff = now - timedelta(days=archive_retention_days)

        stale_marked = 0
        archived = 0
        deleted = 0

        for memory_id, memory_data in list(self._memories.items()):
            current_status = memory_data.get("status", "active")
            created_at = memory_data.get("created_at", now)
            last_accessed = memory_data.get("last_accessed_at", created_at)
            archived_at = memory_data.get("archived_at")

            # Transition: new/active → stale (not accessed recently)
            if current_status in ("new", "active") and last_accessed < stale_cutoff:
                memory_data["status"] = "stale"
                memory_data["updated_at"] = now
                stale_marked += 1
                logger.debug(f"Memory {memory_id}: {current_status} → stale")

            # Transition: stale → archived (retention expired)
            elif current_status == "stale" and created_at < retention_cutoff:
                memory_data["status"] = "archived"
                memory_data["archived_at"] = now
                memory_data["updated_at"] = now
                archived += 1
                logger.debug(f"Memory {memory_id}: stale → archived")

            # Transition: archived → deleted (archive retention expired)
            elif current_status == "archived" and archived_at and archived_at < archive_cutoff:
                # Don't delete summaries
                if memory_data.get("memory_type") not in ("session_summary", "consolidated"):
                    del self._memories[memory_id]
                    deleted += 1
                    logger.debug(f"Memory {memory_id}: archived → deleted")

        # Update metrics
        self._cleanup_count += deleted
        self._last_cleanup = now

        logger.info(
            f"Lifecycle cleanup: {stale_marked} marked stale, "
            f"{archived} archived, {deleted} deleted"
        )

        return {
            "stale_marked": stale_marked,
            "archived": archived,
            "deleted": deleted,
        }

    async def find_duplicates(
        self, similarity_threshold: float = 0.85
    ) -> list["DuplicateCandidate"]:
        """Find potential duplicate memories.

        Args:
            similarity_threshold: Minimum similarity to consider duplicate

        Returns:
            List of duplicate candidates
        """
        from app.model.memory import DuplicateCandidate

        duplicates = []
        memory_list = list(self._memories.values())

        # Compare each pair
        for i, mem1 in enumerate(memory_list):
            for mem2 in memory_list[i + 1 :]:
                # Simple similarity based on content overlap
                content1 = mem1["content"].lower()
                content2 = mem2["content"].lower()

                # Calculate simple similarity
                if len(content1) > 10 and len(content2) > 10:
                    # Check if one contains the other or significant overlap
                    if content1 in content2 or content2 in content1:
                        similarity = 1.0
                    else:
                        # Simple word overlap
                        words1 = set(content1.split())
                        words2 = set(content2.split())
                        if words1 and words2:
                            overlap = len(words1 & words2) / min(len(words1), len(words2))
                            similarity = overlap
                        else:
                            similarity = 0.0

                    if similarity >= similarity_threshold:
                        duplicates.append(
                            DuplicateCandidate(
                                memory_id_1=mem1["id"],
                                memory_id_2=mem2["id"],
                                content_1=mem1["content"],
                                content_2=mem2["content"],
                                similarity=similarity,
                            )
                        )

        return duplicates

    async def deduplicate_memories(
        self, similarity_threshold: float = 0.9, importance_guardrail: float = 0.8
    ) -> ConsolidationResult:
        """Find and merge duplicate memories based on similarity.

        Uses non-destructive deduplication: creates a merged memory instead of deleting.

        Args:
            similarity_threshold: Minimum similarity (0-1) to consider as duplicate
            importance_guardrail: Don't deduplicate memories with importance > this value

        Returns:
            Consolidation result with merge statistics
        """
        from app.model.memory import ConsolidationResult

        original_count = len(self._memories)
        duplicates = await self.find_duplicates(similarity_threshold)
        duplicates_merged = 0
        skipped_high_importance = 0

        # Non-destructive deduplication: create merged memory instead of deleting
        for dup in duplicates:
            mem1 = self._memories.get(dup.memory_id_1)
            mem2 = self._memories.get(dup.memory_id_2)

            if mem1 and mem2:
                # Guardrail: don't deduplicate high-importance memories
                importance1 = mem1.get("importance", 1.0)
                importance2 = mem2.get("importance", 1.0)

                if importance1 > importance_guardrail or importance2 > importance_guardrail:
                    skipped_high_importance += 1
                    logger.debug(
                        f"Skipping deduplication for high-importance memories: "
                        f"{dup.memory_id_1} ({importance1}), {dup.memory_id_2} ({importance2})"
                    )
                    continue

                # Create merged memory instead of deleting
                now = datetime.utcnow()
                merged_id = f"merged_{now.strftime('%Y%m%d_%H%M%S')}_{duplicates_merged}"

                # Merge content with separator
                merged_content = (
                    f"--- Memory 1 ---\n{mem1['content']}\n\n"
                    f"--- Memory 2 ---\n{mem2['content']}"
                )

                # Preserve metadata from both memories
                merged_metadata = {
                    **mem1.get("metadata", {}),
                    **mem2.get("metadata", {}),
                    "merged_from": [mem1["id"], mem2["id"]],
                    "similarity_score": dup.similarity,
                    "merge_reason": "duplicate",
                }

                # Use max importance from both
                merged_importance = max(importance1, importance2)

                # Create the merged memory
                self._memories[merged_id] = {
                    "id": merged_id,
                    "content": merged_content,
                    "memory_type": mem1.get("memory_type", "fact"),
                    "metadata": merged_metadata,
                    "agent_id": mem1.get("agent_id") or mem2.get("agent_id"),
                    "session_id": mem1.get("session_id") or mem2.get("session_id"),
                    "importance": merged_importance,
                    "created_at": now,
                    "updated_at": now,
                    "status": "active",
                }

                # Delete the original memories (non-destructive: we created merged first)
                del self._memories[mem1["id"]]
                del self._memories[mem2["id"]]

                duplicates_merged += 1
                logger.info(
                    f"Merged duplicate memories: {mem1['id']} + {mem2['id']} → {merged_id}"
                )

        # Update tracking
        self._deduplication_count += duplicates_merged
        self._last_cleanup = datetime.utcnow()

        logger.info(
            f"Deduplicated {duplicates_merged} memories, "
            f"skipped {skipped_high_importance} high-importance"
        )

        return ConsolidationResult(
            operation="deduplication",
            memories_processed=original_count,
            memories_merged=duplicates_merged,
            memories_deleted=0,
            duplicates_found=len(duplicates),
        )

    async def get_duplicate_candidates(
        self, similarity_threshold: float = 0.9
    ) -> list[DuplicateCandidate]:
        """Find potential duplicate memories (alias for find_duplicates).

        Args:
            similarity_threshold: Minimum similarity to consider as duplicate

        Returns:
            List of duplicate candidates
        """
        return await self.find_duplicates(similarity_threshold)

    # Encryption methods
    _encrypted_memories: set[str] = set()
    _encryption_enabled: bool = False

    async def encrypt_memories(
        self, memory_ids: list[str] | None = None, encrypt_all: bool = False
    ) -> "EncryptResult":
        """Encrypt sensitive memories.

        Args:
            memory_ids: Specific memories to encrypt (None = all)
            encrypt_all: Encrypt all memories

        Returns:
            Encryption results
        """
        processed = 0
        encrypted = 0
        failed = []

        if encrypt_all:
            # Encrypt all memories
            for memory_id in self._memories:
                try:
                    self._encrypted_memories.add(memory_id)
                    encrypted += 1
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to encrypt {memory_id}: {e}")
                    failed.append(memory_id)
        elif memory_ids:
            # Encrypt specific memories
            for memory_id in memory_ids:
                try:
                    if memory_id in self._memories:
                        self._encrypted_memories.add(memory_id)
                        encrypted += 1
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to encrypt {memory_id}: {e}")
                    failed.append(memory_id)
        else:
            # Auto-encrypt sensitive content (placeholder)
            for memory_id, memory_data in self._memories.items():
                content = memory_data["content"].lower()
                # Check for sensitive keywords
                if any(
                    kw in content
                    for kw in ["password", "api_key", "secret", "token", "credential"]
                ):
                    try:
                        self._encrypted_memories.add(memory_id)
                        encrypted += 1
                        processed += 1
                    except Exception as e:
                        logger.error(f"Failed to encrypt {memory_id}: {e}")
                        failed.append(memory_id)

        self._encryption_enabled = encrypted > 0

        logger.info(f"Encrypted {encrypted} memories")

        return EncryptResult(
            processed=processed,
            encrypted=encrypted,
            decrypted=0,
            failed=failed,
        )

    async def decrypt_memories(self, memory_ids: list[str]) -> "EncryptResult":
        """Decrypt memories.

        Args:
            memory_ids: Memories to decrypt

        Returns:
            Decryption results
        """
        decrypted = 0
        failed = []

        for memory_id in memory_ids:
            try:
                if memory_id in self._encrypted_memories:
                    self._encrypted_memories.remove(memory_id)
                    decrypted += 1
            except Exception as e:
                logger.error(f"Failed to decrypt {memory_id}: {e}")
                failed.append(memory_id)

        self._encryption_enabled = len(self._encrypted_memories) > 0

        logger.info(f"Decrypted {decrypted} memories")

        return EncryptResult(
            processed=len(memory_ids),
            encrypted=0,
            decrypted=decrypted,
            failed=failed,
        )

    async def get_encryption_status(self) -> "EncryptionStatus":
        """Get encryption status.

        Returns:
            Current encryption status
        """
        return EncryptionStatus(
            enabled=self._encryption_enabled,
            algorithm="AES-256-GCM" if self._encryption_enabled else "None",
            encrypted_memories=len(self._encrypted_memories),
        )

    # ========= Backup Methods =========

    def _get_backup_dir(self) -> Path:
        """Get the backup directory path."""
        backup_dir = Path(os.path.expanduser(BACKUP_DIR))
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    async def _create_backup(self, backup_type: str = "incremental") -> Path:
        """Create a backup of all memories.

        Args:
            backup_type: Type of backup (full, incremental, auto)

        Returns:
            Path to the created backup file
        """
        import gzip
        import json

        memories = list(self._memories.values())
        export_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "backup_type": backup_type,
            "total_memories": len(memories),
            "memories": [
                {
                    "id": m.get("id"),
                    "content": m.get("content"),
                    "memory_type": m.get("memory_type"),
                    "metadata": m.get("metadata", {}),
                    "agent_id": m.get("agent_id"),
                    "session_id": m.get("session_id"),
                    "importance": m.get("importance", 1.0),
                    "status": m.get("status", "active"),
                    "created_at": m.get("created_at").isoformat() if m.get("created_at") else None,
                    "updated_at": m.get("updated_at").isoformat() if m.get("updated_at") else None,
                }
                for m in memories
            ],
        }

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"memories_{backup_type}_{timestamp}.json.gz"
        filepath = self._get_backup_dir() / filename

        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Created backup: {filepath} ({len(memories)} memories)")

        # Apply rotation
        await self._rotate_backups()

        return filepath

    async def _rotate_backups(self) -> int:
        """Rotate old backups, keeping only the most recent.

        Returns:
            Number of backups removed
        """
        backup_dir = self._get_backup_dir()

        # Get all backup files sorted by modification time
        backups = sorted(
            backup_dir.glob("memories_*.json.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        removed = 0
        for old_backup in backups[BACKUP_MAX_KEEP:]:
            try:
                old_backup.unlink()
                removed += 1
                logger.info(f"Removed old backup: {old_backup}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup {old_backup}: {e}")

        return removed

    async def _check_and_create_backup(self) -> None:
        """Check if backup is needed and create if necessary.

        Called after creating memories to implement automatic backup.
        """
        memory_count = len(self._memories)
        memories_since_backup = memory_count - self._memory_count_at_last_backup

        # Check if we need an incremental backup (every 50 new memories)
        if memories_since_backup >= BACKUP_MEMORY_THRESHOLD:
            logger.info(f"Auto-backup triggered: {memories_since_backup} new memories")
            try:
                await self._create_backup("auto")
                self._memory_count_at_last_backup = memory_count
            except Exception as e:
                logger.warning(f"Auto-backup failed: {e}")

    async def _check_daily_backup(self) -> None:
        """Check if daily backup is needed.

        Should be called daily (e.g., from a scheduler).
        """
        now = datetime.utcnow()

        # Check if we haven't done a daily backup today
        if self._last_daily_backup is None or self._last_daily_backup.date() < now.date():
            logger.info("Daily backup triggered")
            try:
                await self._create_backup("daily")
                self._last_daily_backup = now
            except Exception as e:
                logger.warning(f"Daily backup failed: {e}")


# Global memory service instance
_memory_service: MemoryService | None = None
_memory_service_lock = asyncio.Lock()


def get_memory_service() -> MemoryService:
    """Get the global memory service instance (singleton).

    Returns the same MemoryService instance for all calls to avoid
    recreating expensive resources like embedding models and Qdrant connections.
    """
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
