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

import gzip
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.model.enums import AccessLevel, MemoryType
from app.model.memory import (
    BackupCreate,
    BackupInfo,
    BackupList,
    CleanupResult,
    ConsolidateResult,
    DecryptRequest,
    DuplicateCandidate,
    EncryptionStatus,
    EncryptRequest,
    EncryptResult,
    ImportRequest,
    ImportResult,
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
    access_level: AccessLevel | None = None,
    project_id: str | None = None,
    memory_type: MemoryType | None = None,
    agent_id: str | None = None,
    limit: int = 100,
):
    """List memories with optional filters.

    Returns a list of memories, optionally filtered by type, agent, project, and access level.
    """
    try:
        service = get_memory_service()
        memories = await service.list_memories(
            access_level=access_level,
            project_id=project_id,
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


# ========= Backup Endpoints =========


def _get_backup_dir() -> Path:
    """Get the backup directory path."""
    backup_dir = Path.home() / ".eigent" / "backups" / "memories"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


@router.get("/export", name="export memories")
async def export_memories():
    """Export all memories to JSON.

    Returns a gzipped JSON file containing all memories.
    """
    try:
        service = get_memory_service()
        memories = await service.list_memories(limit=100000)

        export_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "total_memories": len(memories),
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "memory_type": m.memory_type.value,
                    "metadata": m.metadata,
                    "agent_id": m.agent_id,
                    "session_id": m.session_id,
                    "importance": m.importance,
                    "is_summary": m.is_summary,
                    "summary_level": m.summary_level,
                    "source_memory_ids": m.source_memory_ids,
                    "is_encrypted": m.is_encrypted,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in memories
            ],
        }

        # Create filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"memories_export_{timestamp}.json.gz"
        filepath = _get_backup_dir() / filename

        # Write gzipped JSON
        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(memories)} memories to {filepath}")
        return FileResponse(
            filepath,
            media_type="application/gzip",
            filename=filename,
        )
    except Exception as e:
        logger.error(f"Failed to export memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=ImportResult, name="import memories")
async def import_memories(
    file: UploadFile,
    merge_strategy: str = "skip",
):
    """Import memories from a JSON file.

    Accepts a gzipped JSON file with memories to upload.
    Uses merge_strategy to determine how to handle duplicates:
    - skip: Skip memories with existing IDs
    - update: Update existing memories with same ID
    - replace: Replace all existing memories
    """
    try:
        # Read uploaded file
        content = await file.read()

        # Try to decompress if gzipped
        try:
            with gzip.decompress(content) as decompressed:
                data = json.loads(decompressed)
        except Exception:
            # Try as plain JSON
            data = json.loads(content)

        memories_data = data.get("memories", [])
        logger.info(f"Importing {len(memories_data)} memories from {file.filename}")

        service = get_memory_service()

        imported = 0
        skipped = 0
        updated = 0
        failed = 0
        errors = []

        # Get existing memories
        existing_memories = await service.list_memories(limit=100000)
        existing_ids = {m.id for m in existing_memories}

        for mem_data in memories_data:
            try:
                memory_id = mem_data.get("id")
                memory_type_str = mem_data.get("memory_type", "fact")

                # Check if exists
                if memory_id in existing_ids:
                    if merge_strategy == "skip":
                        skipped += 1
                        continue
                    elif merge_strategy == "update":
                        # Update existing
                        update = MemoryUpdate(
                            content=mem_data.get("content"),
                            metadata=mem_data.get("metadata", {}),
                        )
                        await service.update_memory(memory_id, update)
                        updated += 1
                        continue

                # Create new memory
                create = MemoryCreate(
                    content=mem_data.get("content", ""),
                    memory_type=MemoryType(memory_type_str),
                    metadata=mem_data.get("metadata", {}),
                    agent_id=mem_data.get("agent_id"),
                    session_id=mem_data.get("session_id"),
                )
                await service.create_memory(create)
                imported += 1
            except Exception as e:
                failed += 1
                errors.append(f"Failed to import {mem_data.get('id')}: {str(e)}")

        logger.info(f"Import complete: {imported} imported, {skipped} skipped, {updated} updated, {failed} failed")
        return ImportResult(
            imported=imported,
            skipped=skipped,
            updated=updated,
            failed=failed,
            errors=errors,
        )
    except Exception as e:
        logger.error(f"Failed to import memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup/list", response_model=BackupList, name="list backups")
async def list_backups():
    """List available backups.

    Returns a list of all backup files in the backup directory.
    """
    try:
        backup_dir = _get_backup_dir()
        backups = []

        for filepath in sorted(backup_dir.glob("*.gz"), reverse=True):
            stat = filepath.stat()
            backups.append(
                BackupInfo(
                    filename=filepath.name,
                    path=str(filepath),
                    size_bytes=stat.st_size,
                    memory_count=0,  # Would need to read to get count
                    created_at=datetime.fromtimestamp(stat.st_mtime),
                    backup_type="manual" if "manual" in filepath.name else "full",
                )
            )

        total_size = sum(b.size_bytes for b in backups)
        return BackupList(backups=backups, total_size_bytes=total_size)
    except Exception as e:
        logger.error(f"Failed to list backups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/create", response_model=BackupInfo, name="create backup")
async def create_backup(request: BackupCreate):
    """Create a manual backup.

    Creates a new backup of all memories.
    """
    try:
        service = get_memory_service()
        memories = await service.list_memories(limit=100000)

        export_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "total_memories": len(memories),
            "backup_type": request.backup_type,
            "description": request.description,
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "memory_type": m.memory_type.value,
                    "metadata": m.metadata,
                    "agent_id": m.agent_id,
                    "session_id": m.session_id,
                    "importance": m.importance,
                    "is_summary": m.is_summary,
                    "summary_level": m.summary_level,
                    "source_memory_ids": m.source_memory_ids,
                    "is_encrypted": m.is_encrypted,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in memories
            ],
        }

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_type_str = request.backup_type or "manual"
        filename = f"memories_{backup_type_str}_{timestamp}.json.gz"
        filepath = _get_backup_dir() / filename

        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        stat = filepath.stat()
        logger.info(f"Created backup: {filepath} ({len(memories)} memories)")

        return BackupInfo(
            filename=filename,
            path=str(filepath),
            size_bytes=stat.st_size,
            memory_count=len(memories),
            created_at=datetime.fromtimestamp(stat.st_mtime),
            backup_type=backup_type_str,
        )
    except Exception as e:
        logger.error(f"Failed to create backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
