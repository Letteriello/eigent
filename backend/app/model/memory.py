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

from app.model.enums import MemoryType


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
