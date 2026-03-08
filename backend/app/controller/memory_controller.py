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

"""Memory controller for persistent agent memory API endpoints."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.model.enums import MemoryType
from app.model.memory import (
    CleanupResult,
    ConsolidateResult,
    DecryptRequest,
    DuplicateCandidate,
    EncryptionStatus,
    EncryptRequest,
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
from app.service.memory_service import get_memory_service

logger = logging.getLogger("memory_controller")

router = APIRouter(prefix="/api/memory", tags=["Memory"])


class DeleteResponse(BaseModel):
    """Response for delete operations."""

    success: bool
    message: str


@router.post("", response_model=MemoryResponse, name="create memory")
async def create_memory(memory: MemoryCreate):
    """Create a new memory entry.

    Stores a new memory with content, type, and optional metadata.
    The memory is indexed for both vector and keyword search.
    """
    try:
        service = get_memory_service()
        result = await service.create_memory(memory)
        logger.info(f"Created memory: {result.id}")
        return result
    except Exception as e:
        logger.error(f"Failed to create memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}", response_model=MemoryResponse, name="get memory")
async def get_memory(memory_id: str):
    """Get a memory by ID.

    Retrieves a specific memory entry by its unique identifier.
    """
    try:
        service = get_memory_service()
        memory = await service.get_memory(memory_id)

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{memory_id}", response_model=MemoryResponse, name="update memory")
async def update_memory(memory_id: str, update: MemoryUpdate):
    """Update an existing memory.

    Updates the content, type, or metadata of an existing memory entry.
    """
    try:
        service = get_memory_service()
        memory = await service.update_memory(memory_id, update)

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        logger.info(f"Updated memory: {memory_id}")
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}", response_model=DeleteResponse, name="delete memory")
async def delete_memory(memory_id: str):
    """Delete a memory.

    Removes a memory entry from the storage.
    """
    try:
        service = get_memory_service()
        deleted = await service.delete_memory(memory_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Memory not found")

        logger.info(f"Deleted memory: {memory_id}")
        return DeleteResponse(success=True, message=f"Memory {memory_id} deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[MemoryResponse], name="list memories")
async def list_memories(
    memory_type: MemoryType | None = None,
    agent_id: str | None = None,
    limit: int = 100,
):
    """List memories with optional filters.

    Returns a list of memories, optionally filtered by type and agent.
    """
    try:
        service = get_memory_service()
        memories = await service.list_memories(
            memory_type=memory_type,
            agent_id=agent_id,
            limit=limit,
        )
        return memories
    except Exception as e:
        logger.error(f"Failed to list memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=MemorySearchResult, name="search memories")
async def search_memories(search_query: MemorySearchQuery):
    """Search memories using hybrid search.

    Performs semantic (vector) and keyword (BM25) search,
    combining results using Reciprocal Rank Fusion.
    """
    try:
        service = get_memory_service()
        results = await service.search_memories(search_query)
        return results
    except Exception as e:
        logger.error(f"Failed to search memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=MemoryStats, name="memory stats")
async def get_memory_stats():
    """Get memory statistics.

    Returns aggregated statistics about stored memories.
    """
    try:
        service = get_memory_service()
        stats = await service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========= Summarization Endpoints =========


@router.post(
    "/{memory_id}/summarize",
    response_model=MemoryResponse,
    name="summarize memory",
)
async def summarize_memory(memory_id: str, request: MemorySummaryRequest):
    """Summarize a specific memory.

    Generates a summary of the given memory based on the specified level.
    """
    try:
        service = get_memory_service()
        memory = await service.summarize_memory(memory_id, request)

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        logger.info(f"Summarized memory: {memory_id}")
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to summarize memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/summaries/pending",
    response_model=list[PendingSummary],
    name="pending summaries",
)
async def get_pending_summaries(limit: int = 20):
    """Get memories pending summarization.

    Returns a list of memories that haven't been summarized yet.
    """
    try:
        service = get_memory_service()
        pending = await service.get_pending_summaries(limit)
        return pending
    except Exception as e:
        logger.error(f"Failed to get pending summaries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========= Consolidation Endpoints =========


@router.post("/consolidate", response_model=ConsolidateResult, name="consolidate memories")
async def consolidate_memories():
    """Run memory deduplication and consolidation.

    Finds and merges duplicate memories, creates consolidated summaries.
    """
    try:
        service = get_memory_service()
        result = await service.consolidate_memories()
        logger.info(f"Consolidation complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to consolidate memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup", response_model=CleanupResult, name="cleanup memories")
async def cleanup_memories(days: int = 30):
    """Clean up old memories.

    Removes memories older than the specified number of days.
    """
    try:
        service = get_memory_service()
        result = await service.cleanup_old_memories(days)
        logger.info(f"Cleanup complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to cleanup memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/duplicates",
    response_model=list[DuplicateCandidate],
    name="find duplicates",
)
async def find_duplicates(similarity_threshold: float = 0.85):
    """Find potential duplicate memories.

    Returns a list of memories that may be duplicates.
    """
    try:
        service = get_memory_service()
        duplicates = await service.find_duplicates(similarity_threshold)
        return duplicates
    except Exception as e:
        logger.error(f"Failed to find duplicates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========= Encryption Endpoints =========


@router.post("/encrypt", response_model=EncryptResult, name="encrypt memories")
async def encrypt_memories(request: EncryptRequest):
    """Encrypt sensitive memories.

    Encrypts memories containing sensitive information.
    """
    try:
        service = get_memory_service()
        result = await service.encrypt_memories(
            memory_ids=request.memory_ids if request.memory_ids else None,
            encrypt_all=request.encrypt_all,
        )
        logger.info(f"Encryption complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to encrypt memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decrypt", response_model=EncryptResult, name="decrypt memories")
async def decrypt_memories(request: DecryptRequest):
    """Decrypt memories.

    Decrypts previously encrypted memories.
    """
    try:
        service = get_memory_service()
        result = await service.decrypt_memories(request.memory_ids)
        logger.info(f"Decryption complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to decrypt memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/encryption-status",
    response_model=EncryptionStatus,
    name="encryption status",
)
async def get_encryption_status():
    """Get encryption status.

    Returns current encryption settings and status.
    """
    try:
        service = get_memory_service()
        status = await service.get_encryption_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get encryption status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========= Settings Endpoints =========


@router.get("/settings", response_model=MemorySettings, name="memory settings")
async def get_memory_settings():
    """Get memory settings.

    Returns current memory configuration.
    """
    try:
        service = get_memory_service()
        settings = await service.get_settings()
        return settings
    except Exception as e:
        logger.error(f"Failed to get memory settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", response_model=MemorySettings, name="update memory settings")
async def update_memory_settings(settings: MemorySettings):
    """Update memory settings.

    Modifies memory configuration.
    """
    try:
        service = get_memory_service()
        updated = await service.update_settings(settings)
        logger.info("Updated memory settings")
        return updated
    except Exception as e:
        logger.error(f"Failed to update memory settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
