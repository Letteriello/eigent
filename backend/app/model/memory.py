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

"""Memory models for persistent agent memory storage."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.model.enums import MemoryType, SummaryLevel


class MemoryCreate(BaseModel):
    """Schema for creating a new memory entry."""

    content: str = Field(..., description="The memory content/text")
    memory_type: MemoryType = Field(
        default=MemoryType.fact,
        description="Type of memory (fact, preference, context, learned)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the memory",
    )
    agent_id: str | None = Field(
        default=None,
        description="Optional agent ID this memory belongs to",
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for session-scoped memories",
    )


class MemoryUpdate(BaseModel):
    """Schema for updating an existing memory entry."""

    content: str | None = Field(
        default=None,
        description="Updated memory content",
    )
    memory_type: MemoryType | None = Field(
        default=None,
        description="Updated memory type",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Updated metadata",
    )


class MemoryResponse(BaseModel):
    """Schema for memory response from API."""

    id: str = Field(..., description="Unique memory identifier")
    content: str = Field(..., description="The memory content/text")
    memory_type: MemoryType = Field(..., description="Type of memory")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    agent_id: str | None = Field(
        default=None,
        description="Agent ID this memory belongs to",
    )
    session_id: str | None = Field(
        default=None,
        description="Session ID for session-scoped memories",
    )
    importance: float = Field(
        default=1.0,
        description="Importance score (0-1) for memory prioritization",
    )
    is_summary: bool = Field(
        default=False,
        description="Whether this memory is a summary of other memories",
    )
    summary_level: str | None = Field(
        default=None,
        description="Level of summarization: session, consolidated, key_facts",
    )
    source_memory_ids: list[str] = Field(
        default_factory=list,
        description="IDs of memories that were summarized",
    )
    is_encrypted: bool = Field(
        default=False,
        description="Whether this memory's content is encrypted",
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class MemorySearchQuery(BaseModel):
    """Schema for memory search requests."""

    query: str = Field(..., description="Search query text")
    memory_type: MemoryType | None = Field(
        default=None,
        description="Filter by memory type",
    )
    agent_id: str | None = Field(
        default=None,
        description="Filter by agent ID",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of results to return",
    )
    similarity_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score",
    )


class MemorySearchResult(BaseModel):
    """Schema for memory search results."""

    memories: list[MemoryResponse] = Field(
        ...,
        description="List of matching memories",
    )
    total: int = Field(..., description="Total number of matches")
    query: str = Field(..., description="Original search query")


class ConsolidationResult(BaseModel):
    """Result of consolidation operation."""

    operation: str = Field(..., description="Operation type")
    memories_processed: int = Field(..., description="Number of memories processed")
    memories_merged: int = Field(..., description="Number of memories merged")
    memories_deleted: int = Field(..., description="Number of memories deleted")
    duplicates_found: int = Field(..., description="Number of duplicate candidates found")


class MemorySettings(BaseModel):
    """Schema for memory settings."""

    max_memories: int = Field(
        default=10000,
        ge=100,
        description="Maximum number of memories to store",
    )
    auto_summarize: bool = Field(
        default=True,
        description="Automatically summarize memories after sessions",
    )
    summarization_threshold: int = Field(
        default=50,
        ge=10,
        le=500,
        description="Number of memories before triggering consolidation",
    )
    retention_days: int = Field(
        default=90,
        ge=7,
        description="Days to retain memories before cleanup",
    )
    encryption_enabled: bool = Field(
        default=False,
        description="Whether encryption is enabled for sensitive memories",
    )
    auto_cleanup: bool = Field(
        default=True,
        description="Automatically clean up old memories",
    )


class MemorySummaryRequest(BaseModel):
    """Schema for requesting memory summarization."""

    level: SummaryLevel = Field(
        default=SummaryLevel.session,
        description="Level of summarization",
    )
    force: bool = Field(
        default=False,
        description="Force re-summarization even if already summarized",
    )


class PendingSummary(BaseModel):
    """Schema for pending summary information."""

    memory_id: str = Field(..., description="Memory ID")
    content_preview: str = Field(..., description="Preview of memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    created_at: datetime = Field(..., description="Creation timestamp")
    agent_id: str | None = Field(default=None, description="Agent ID")


class DuplicateCandidate(BaseModel):
    """Schema for duplicate memory candidates."""

    memory_id_1: str = Field(..., description="First memory ID")
    memory_id_2: str = Field(..., description="Second memory ID")
    content_1: str = Field(..., description="Content of first memory")
    content_2: str = Field(..., description="Content of second memory")
    similarity: float = Field(..., description="Similarity score")


class EncryptRequest(BaseModel):
    """Schema for encrypting memories."""

    memory_ids: list[str] = Field(
        default_factory=list,
        description="List of memory IDs to encrypt (empty = all sensitive)",
    )
    encrypt_all: bool = Field(
        default=False,
        description="Encrypt all memories",
    )


class DecryptRequest(BaseModel):
    """Schema for decrypting memories."""

    memory_ids: list[str] = Field(
        ...,
        description="List of memory IDs to decrypt",
    )


class EncryptResult(BaseModel):
    """Schema for encryption/decryption results."""

    processed: int = Field(..., description="Number of memories processed")
    encrypted: int = Field(..., description="Number of memories encrypted")
    decrypted: int = Field(..., description="Number of memories decrypted")
    failed: list[str] = Field(
        default_factory=list,
        description="List of memory IDs that failed",
    )


class ConsolidateResult(BaseModel):
    """Schema for consolidation results."""

    original_count: int = Field(..., description="Original memory count")
    consolidated_count: int = Field(..., description="Consolidated memory count")
    duplicates_found: int = Field(..., description="Duplicates found")
    duplicates_merged: int = Field(..., description="Duplicates merged")
    summaries_created: int = Field(..., description="Summaries created")


class CleanupResult(BaseModel):
    """Schema for cleanup results."""

    deleted_count: int = Field(..., description="Number of memories deleted")
    freed_space: int = Field(..., description="Estimated bytes freed")


class EncryptionStatus(BaseModel):
    """Schema for encryption status."""

    enabled: bool = Field(..., description="Whether encryption is enabled")
    algorithm: str = Field(..., description="Encryption algorithm used")
    encrypted_memories: int = Field(..., description="Number of encrypted memories")


class MemoryStats(BaseModel):
    """Schema for memory statistics."""

    total_memories: int = Field(..., description="Total number of memories")
    by_type: dict[str, int] = Field(
        ...,
        description="Memory count by type",
    )
    by_agent: dict[str, int] = Field(
        default_factory=dict,
        description="Memory count by agent",
    )
    deduplication_count: int = Field(
        default=0,
        description="Total memories deduplicated",
    )
    cleanup_count: int = Field(
        default=0,
        description="Total memories cleaned up",
    )
    last_cleanup: datetime | None = Field(
        default=None,
        description="Last cleanup timestamp",
    )
