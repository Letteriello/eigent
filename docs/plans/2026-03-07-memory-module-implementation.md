# Memory Module Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement persistent memory module for AI agents enabling recall of facts, preferences, context, and learned information across sessions.

**Architecture:** Extended RAG architecture using Qdrant for vector storage + SQLite for metadata, with hybrid search (BM25 + semantic embeddings).

**Tech Stack:** FastAPI, Qdrant, OpenAI Embeddings, React, TypeScript, Zustand

---

## Fase 1: Backend Core (Models, Service, Controller)

### Task 1: Create MemoryType Enum

**Files:**
- Modify: `backend/app/model/enums.py`

**Step 1: Add the enum**

```python
class MemoryType(str, Enum):
    """Types of agent memory"""
    FACT = "fact"           # Facts learned about user/environment
    PREFERENCE = "preference"  # User preferences
    CONTEXT = "context"    # Working context
    LEARNED = "learned"   # General learnings
```

**Step 2: Commit**

---

### Task 2: Create Memory Models (Pydantic)

**Files:**
- Create: `backend/app/model/memory.py`

**Step 1: Write the models**

```python
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    CONTEXT = "context"
    LEARNED = "learned"


class MemoryBase(BaseModel):
    """Base memory fields"""
    content: str = Field(..., description="Memory content text")
    memory_type: MemoryType = Field(default=MemoryType.CONTEXT)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryCreate(MemoryBase):
    """Memory creation request"""
    pass


class MemoryUpdate(BaseModel):
    """Memory update request"""
    content: str | None = None
    memory_type: MemoryType | None = None
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] | None = None


class AgentMemory(MemoryBase):
    """Full memory model with ID and timestamps"""
    id: UUID = Field(default_factory=uuid.uuid4)
    agent_id: str = Field(..., description="Agent ID that owns this memory")
    embedding: list[float] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class MemorySearchParams(BaseModel):
    """Search parameters for hybrid search"""
    query: str
    limit: int = Field(default=5, ge=1, le=50)
    memory_type: MemoryType | None = None
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)


class MemorySearchResult(BaseModel):
    """Search result with score"""
    memory: AgentMemory
    score: float
    source: str  # "vector" | "bm25" | "hybrid"
```

**Step 2: Add to model __init__**

In `backend/app/model/__init__.py`:
```python
from app.model.memory import (
    AgentMemory,
    MemoryCreate,
    MemorySearchParams,
    MemorySearchResult,
    MemoryType,
    MemoryUpdate,
)

__all__ = [
    "AgentMemory",
    "MemoryCreate",
    "MemorySearchParams",
    "MemorySearchResult",
    "MemoryType",
    "MemoryUpdate",
]
```

**Step 3: Commit**

---

### Task 3: Create Memory Service (CRUD + Qdrant)

**Files:**
- Create: `backend/app/service/memory_service.py`

**Step 1: Write the service**

```python
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
import logging
import os
from pathlib import Path
from uuid import UUID

from numpy import dot
from numpy.linalg import norm
from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.model.memory import (
    AgentMemory,
    MemoryCreate,
    MemorySearchParams,
    MemorySearchResult,
    MemoryType,
    MemoryUpdate,
)

logger = logging.getLogger("memory_service")

# Configuration
EMBEDDING_MODEL = os.getenv("MEMORY_EMBEDDING_MODEL", "text-embedding-ada-002")
EMBEDDING_DIM = int(os.getenv("MEMORY_EMBEDDING_DIM", "1536"))
QDRANT_PATH = os.getenv("MEMORY_QDRANT_PATH", "~/.eigent/qdrant")


class MemoryService:
    """Service for managing agent memory with Qdrant storage"""

    def __init__(self):
        self._client: QdrantClient | None = None
        self._openai_client: AsyncOpenAI | None = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            path = Path(QDRANT_PATH).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=str(path))
        return self._client

    @property
    def openai_client(self) -> AsyncOpenAI:
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI()
        return self._openai_client

    def _get_collection_name(self, agent_id: str) -> str:
        return f"agent_{agent_id}_memory"

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using OpenAI"""
        response = await self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def _ensure_collection(self, agent_id: str) -> None:
        """Ensure collection exists for agent"""
        collection_name = self._get_collection_name(agent_id)
        collections = self.client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {collection_name}")

    async def create_memory(
        self, agent_id: str, data: MemoryCreate
    ) -> AgentMemory:
        """Create a new memory for an agent"""
        self._ensure_collection(agent_id)

        # Get embedding
        embedding = await self._get_embedding(data.content)

        # Create memory object
        memory = AgentMemory(
            agent_id=agent_id,
            content=data.content,
            memory_type=data.memory_type,
            importance=data.importance,
            metadata=data.metadata,
            embedding=embedding,
        )

        # Store in Qdrant
        self.client.upsert(
            collection_name=self._get_collection_name(agent_id),
            points=[
                PointStruct(
                    id=str(memory.id),
                    vector=embedding,
                    payload={
                        "content": memory.content,
                        "memory_type": memory.memory_type.value,
                        "importance": memory.importance,
                        "metadata": memory.metadata,
                        "created_at": memory.created_at.isoformat(),
                        "updated_at": memory.updated_at.isoformat(),
                    }
                )
            ]
        )

        logger.info(f"Created memory {memory.id} for agent {agent_id}")
        return memory

    async def get_memory(self, agent_id: str, memory_id: UUID) -> AgentMemory | None:
        """Get a specific memory"""
        collection_name = self._get_collection_name(agent_id)
        result = self.client.retrieve(
            collection_name=collection_name,
            ids=[str(memory_id)]
        )

        if not result:
            return None

        return self._from_payload(result[0], agent_id, result[0].vector)

    async def list_memories(
        self,
        agent_id: str,
        memory_type: MemoryType | None = None,
        limit: int = 100
    ) -> list[AgentMemory]:
        """List all memories for an agent"""
        collection_name = self._get_collection_name(agent_id)

        # Note: Qdrant scroll returns all, filter in memory for type
        results = self.client.scroll(
            collection_name=collection_name,
            limit=limit,
            with_vectors=True
        )

        memories = []
        for point in results[0]:
            if memory_type and point.payload.get("memory_type") != memory_type.value:
                continue
            memories.append(self._from_payload(point, agent_id, point.vector))

        return memories

    async def update_memory(
        self, agent_id: str, memory_id: UUID, data: MemoryUpdate
    ) -> AgentMemory | None:
        """Update an existing memory"""
        existing = await self.get_memory(agent_id, memory_id)
        if not existing:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing, key, value)
        existing.updated_at = __import__("datetime").datetime.utcnow()

        # Regenerate embedding if content changed
        if "content" in update_data:
            existing.embedding = await self._get_embedding(existing.content)

        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self._get_collection_name(agent_id),
            points=[
                PointStruct(
                    id=str(existing.id),
                    vector=existing.embedding,
                    payload={
                        "content": existing.content,
                        "memory_type": existing.memory_type.value,
                        "importance": existing.importance,
                        "metadata": existing.metadata,
                        "created_at": existing.created_at.isoformat(),
                        "updated_at": existing.updated_at.isoformat(),
                    }
                )
            ]
        )

        logger.info(f"Updated memory {memory_id}")
        return existing

    async def delete_memory(self, agent_id: str, memory_id: UUID) -> bool:
        """Delete a memory"""
        collection_name = self._get_collection_name(agent_id)
        self.client.delete(
            collection_name=collection_name,
            points_selector=[str(memory_id)]
        )
        logger.info(f"Deleted memory {memory_id}")
        return True

    async def delete_all_memories(self, agent_id: str) -> bool:
        """Delete all memories for an agent"""
        collection_name = self._get_collection_name(agent_id)
        self.client.delete_collection(collection_name=collection_name)
        logger.info(f"Deleted all memories for agent {agent_id}")
        return True

    def _from_payload(self, payload, agent_id: str, vector: list[float]) -> AgentMemory:
        """Convert Qdrant payload to AgentMemory"""
        from datetime import datetime
        return AgentMemory(
            id=UUID(payload.id),
            agent_id=agent_id,
            content=payload.payload["content"],
            memory_type=MemoryType(payload.payload["memory_type"]),
            importance=payload.payload.get("importance", 0.5),
            metadata=payload.payload.get("metadata", {}),
            embedding=vector,
            created_at=datetime.fromisoformat(payload.payload["created_at"]),
            updated_at=datetime.fromisoformat(payload.payload["updated_at"]),
        )


# Singleton instance
memory_service = MemoryService()
```

**Step 2: Commit**

---

### Task 4: Create Memory Controller (REST API)

**Files:**
- Create: `backend/app/controller/memory_controller.py`

**Step 1: Write the controller**

```python
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.model.memory import (
    AgentMemory,
    MemoryCreate,
    MemorySearchParams,
    MemorySearchResult,
    MemoryType,
    MemoryUpdate,
)
from app.service.memory_service import memory_service

logger = logging.getLogger("memory_controller")
router = APIRouter(prefix="/api/memory", tags=["memory"])


class SearchResponse(BaseModel):
    """Search results response"""
    results: list[MemorySearchResult]
    total: int


@router.post("/{agent_id}", response_model=AgentMemory, name="create memory")
async def create_memory(agent_id: str, data: MemoryCreate):
    """Create a new memory for an agent"""
    return await memory_service.create_memory(agent_id, data)


@router.get("/{agent_id}", response_model=list[AgentMemory], name="list memories")
async def list_memories(
    agent_id: str,
    memory_type: MemoryType | None = None,
    limit: int = Query(default=100, ge=1, le=500)
):
    """List all memories for an agent"""
    return await memory_service.list_memories(agent_id, memory_type, limit)


@router.get("/{agent_id}/search", response_model=SearchResponse, name="search memories")
async def search_memories(
    agent_id: str,
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=5, ge=1, le=50),
    memory_type: MemoryType | None = None,
    min_importance: float = Query(default=0.0, ge=0.0, le=1.0),
):
    """Search memories using hybrid search"""
    params = MemorySearchParams(
        query=query,
        limit=limit,
        memory_type=memory_type,
        min_importance=min_importance
    )
    # TODO: Implement hybrid search in Task 7
    results = await memory_service.search(agent_id, params)
    return SearchResponse(results=results, total=len(results))


@router.get("/{agent_id}/{memory_id}", response_model=AgentMemory, name="get memory")
async def get_memory(agent_id: str, memory_id: UUID):
    """Get a specific memory"""
    memory = await memory_service.get_memory(agent_id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.put("/{agent_id}/{memory_id}", response_model=AgentMemory, name="update memory")
async def update_memory(agent_id: str, memory_id: UUID, data: MemoryUpdate):
    """Update a memory"""
    memory = await memory_service.update_memory(agent_id, memory_id, data)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/{agent_id}/{memory_id}", name="delete memory")
async def delete_memory(agent_id: str, memory_id: UUID):
    """Delete a memory"""
    await memory_service.delete_memory(agent_id, memory_id)
    return {"status": "deleted"}


@router.delete("/agent/{agent_id}/all", name="delete all memories")
async def delete_all_memories(agent_id: str):
    """Delete all memories for an agent"""
    await memory_service.delete_all_memories(agent_id)
    return {"status": "all deleted"}
```

**Step 2: Register router in main.py**

In `backend/app/main.py`, find where other routers are registered and add:

```python
from app.controller.memory_controller import router as memory_router

app.include_router(memory_router)
```

**Step 3: Commit**

---

## Fase 2: Busca Híbrida (BM25 + RRF)

### Task 5: Install BM25 Dependency

**Step 1: Add to pyproject.toml**

In `backend/pyproject.toml`, add to dependencies:
```toml
rank-bm25 = "^0.2"
```

**Step 2: Run sync**

```bash
cd backend && uv sync
```

**Step 3: Commit**

---

### Task 6: Implement BM25 Search in Memory Service

**Files:**
- Modify: `backend/app/service/memory_service.py`

**Step 1: Add BM25 search method**

Add these imports at the top:
```python
from rank_bm25 import BM25Okapi
import re
```

Add new method to MemoryService class:
```python
async def _bm25_search(
    self,
    agent_id: str,
    query: str,
    limit: int = 10,
    memory_type: MemoryType | None = None,
    min_importance: float = 0.0
) -> list[tuple[AgentMemory, float]]:
    """BM25 text-based search"""
    memories = await self.list_memories(agent_id, memory_type, limit=500)

    # Filter by importance
    memories = [m for m in memories if m.importance >= min_importance]

    if not memories:
        return []

    # Tokenize content
    def tokenize(text: str) -> list[str]:
        # Simple tokenization: lowercase, remove special chars
        return re.findall(r'\w+', text.lower())

    tokenized_corpus = [tokenize(m.content) for m in memories]
    tokenized_query = tokenize(query)

    if not any(tokenized_corpus):
        return []

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(tokenized_query)

    # Get top results
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append((memories[idx], scores[idx]))

    return results
```

**Step 2: Commit**

---

### Task 7: Implement Hybrid Search (RRF)

**Files:**
- Modify: `backend/app/service/memory_service.py`

**Step 1: Add vector search method**

Add method to MemoryService class:
```python
async def _vector_search(
    self,
    agent_id: str,
    query: str,
    limit: int = 10,
    memory_type: MemoryType | None = None,
    min_importance: float = 0.0
) -> list[tuple[AgentMemory, float]]:
    """Vector-based semantic search"""
    query_embedding = await self._get_embedding(query)
    collection_name = self._get_collection_name(agent_id)

    # Search with filter
    search_params = {
        "limit": limit * 2,  # Get more for filtering
    }

    # Note: Qdrant filter syntax
    must_filters = []
    if memory_type:
        must_filters.append({
            "key": "memory_type",
            "match": {"value": memory_type.value}
        })
    if min_importance > 0:
        must_filters.append({
            "key": "importance",
            "gte": min_importance
        })

    if must_filters:
        search_params["query_filter"] = {"must": must_filters}

    results = self.client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        **search_params
    )

    search_results = []
    for r in results:
        if r.score > 0.1:  # Minimum threshold
            memory = self._from_payload(
                type('Point', (), {
                    'id': r.id,
                    'payload': r.payload,
                    'vector': r.vector
                })(),
                agent_id,
                r.vector
            )
            search_results.append((memory, r.score))

    return search_results[:limit]
```

**Step 2: Add hybrid search method (RRF)**

```python
async def search(
    self,
    agent_id: str,
    params: MemorySearchParams
) -> list[MemorySearchResult]:
    """Hybrid search combining BM25 and vector search using RRF"""

    # Run both searches in parallel
    import asyncio
    bm25_results, vector_results = await asyncio.gather(
        self._bm25_search(
            agent_id,
            params.query,
            params.limit * 2,
            params.memory_type,
            params.min_importance
        ),
        self._vector_search(
            agent_id,
            params.query,
            params.limit * 2,
            params.memory_type,
            params.min_importance
        )
    )

    # Reciprocal Rank Fusion
    k = 60  # RRF parameter
    rrf_scores: dict[str, float] = {}

    # Add BM25 scores (normalize by max)
    max_bm25 = max((s for _, s in bm25_results), default=1.0)
    for memory, score in bm25_results:
        memory_id = str(memory.id)
        normalized_score = score / max_bm25 if max_bm25 > 0 else 0
        rrf_scores[memory_id] = rrf_scores.get(memory_id, 0) + normalized_score / k

    # Add vector scores
    max_vector = max((s for _, s in vector_results), default=1.0)
    for memory, score in vector_results:
        memory_id = str(memory.id)
        normalized_score = score / max_vector if max_vector > 0 else 0
        rrf_scores[memory_id] = rrf_scores.get(memory_id, 0) + normalized_score / k

    # Sort by RRF score
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    # Build results
    memory_map = {str(m.id): m for m, _ in bm25_results}
    memory_map.update({str(m.id): m for m, _ in vector_results})

    results = []
    for memory_id in sorted_ids[:params.limit]:
        memory = memory_map[memory_id]
        score = rrf_scores[memory_id]
        source = "hybrid"
        if memory_id in [str(m.id) for m, _ in bm25_results] and \
           memory_id not in [str(m.id) for m, _ in vector_results]:
            source = "bm25"
        elif memory_id in [str(m.id) for m, _ in vector_results] and \
             memory_id not in [str(m.id) for m, _ in bm25_results]:
            source = "vector"

        results.append(MemorySearchResult(
            memory=memory,
            score=score,
            source=source
        ))

    return results
```

**Step 3: Commit**

---

## Fase 3: Frontend (Memory UI)

### Task 8: Create Memory Store (Zustand)

**Files:**
- Create: `src/store/memoryStore.ts`

**Step 1: Write the store**

```typescript
import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

export type MemoryType = 'fact' | 'preference' | 'context' | 'learned';

export interface AgentMemory {
  id: string;
  agent_id: string;
  content: string;
  memory_type: MemoryType;
  importance: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateMemoryDTO {
  content: string;
  memory_type: MemoryType;
  importance: number;
  metadata?: Record<string, unknown>;
}

export interface UpdateMemoryDTO {
  content?: string;
  memory_type?: MemoryType;
  importance?: number;
  metadata?: Record<string, unknown>;
}

export interface MemorySearchResult {
  memory: AgentMemory;
  score: number;
  source: 'vector' | 'bm25' | 'hybrid';
}

interface MemoryState {
  memories: AgentMemory[];
  loading: boolean;
  searchResults: MemorySearchResult[];
  searchLoading: boolean;
  error: string | null;

  // Actions
  fetchMemories: (agentId: string) => Promise<void>;
  searchMemories: (agentId: string, query: string, memoryType?: MemoryType) => Promise<void>;
  createMemory: (agentId: string, data: CreateMemoryDTO) => Promise<AgentMemory>;
  updateMemory: (agentId: string, memoryId: string, data: UpdateMemoryDTO) => Promise<void>;
  deleteMemory: (agentId: string, memoryId: string) => Promise<void>;
  clearError: () => void;
}

const API_BASE = '/api/memory';

export const useMemoryStore = create<MemoryState>((set, get) => ({
  memories: [],
  loading: false,
  searchResults: [],
  searchLoading: false,
  error: null,

  fetchMemories: async (agentId: string) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/${agentId}`);
      if (!response.ok) throw new Error('Failed to fetch memories');
      const memories = await response.json();
      set({ memories, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  searchMemories: async (agentId: string, query: string, memoryType?: MemoryType) => {
    set({ searchLoading: true, error: null });
    try {
      const params = new URLSearchParams({ query, limit: '10' });
      if (memoryType) params.append('memory_type', memoryType);
      const response = await fetch(`${API_BASE}/${agentId}/search?${params}`);
      if (!response.ok) throw new Error('Search failed');
      const data = await response.json();
      set({ searchResults: data.results, searchLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, searchLoading: false });
    }
  },

  createMemory: async (agentId: string, data: CreateMemoryDTO) => {
    set({ error: null });
    try {
      const response = await fetch(`${API_BASE}/${agentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create memory');
      const memory = await response.json();
      set((state) => ({ memories: [...state.memories, memory] }));
      return memory;
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  updateMemory: async (agentId: string, memoryId: string, data: UpdateMemoryDTO) => {
    set({ error: null });
    try {
      const response = await fetch(`${API_BASE}/${agentId}/${memoryId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update memory');
      const updated = await response.json();
      set((state) => ({
        memories: state.memories.map((m) => m.id === memoryId ? updated : m),
      }));
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  deleteMemory: async (agentId: string, memoryId: string) => {
    set({ error: null });
    try {
      const response = await fetch(`${API_BASE}/${agentId}/${memoryId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete memory');
      set((state) => ({
        memories: state.memories.filter((m) => m.id !== memoryId),
      }));
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));
```

**Step 2: Commit**

---

### Task 9: Create Memory UI (React)

**Files:**
- Modify: `src/pages/Agents/Memory.tsx`

**Step 1: Replace the Coming Soon content**

```tsx
// ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
import { useEffect, useState } from 'react';
import { Brain, Plus, Search, Trash2, Edit2, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useMemoryStore, MemoryType, AgentMemory } from '@/store/memoryStore';

const MEMORY_TYPE_COLORS: Record<MemoryType, string> = {
  fact: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  preference: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  context: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  learned: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
};

const MEMORY_TYPE_LABELS: Record<MemoryType, string> = {
  fact: 'agents.memory.types.fact',
  preference: 'agents.memory.types.preference',
  context: 'agents.memory.types.context',
  learned: 'agents.memory.types.learned',
};

export default function Memory() {
  const { t } = useTranslation();
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<MemoryType | ''>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingMemory, setEditingMemory] = useState<AgentMemory | null>(null);

  const {
    memories,
    loading,
    searchResults,
    searchLoading,
    error,
    fetchMemories,
    searchMemories,
    createMemory,
    updateMemory,
    deleteMemory,
    clearError,
  } = useMemoryStore();

  // Demo agent ID - in real app would come from route/context
  const agentId = selectedAgentId || 'demo-agent';

  useEffect(() => {
    if (searchQuery) {
      searchMemories(agentId, searchQuery, filterType || undefined);
    } else {
      fetchMemories(agentId);
    }
  }, [agentId, searchQuery, filterType]);

  const handleCreate = async (data: { content: string; memory_type: MemoryType; importance: number }) => {
    await createMemory(agentId, data);
    setShowCreateModal(false);
  };

  const handleUpdate = async (data: { content: string; memory_type: MemoryType; importance: number }) => {
    if (editingMemory) {
      await updateMemory(agentId, editingMemory.id, data);
      setEditingMemory(null);
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (confirm(t('agents.memory.confirm-delete'))) {
      await deleteMemory(agentId, memoryId);
    }
  };

  const displayMemories = searchQuery ? searchResults.map(r => r.memory) : memories;

  return (
    <div className="m-auto flex h-auto w-full flex-1 flex-col">
      {/* Header */}
      <div className="flex w-full items-center justify-between px-6 pb-6 pt-8">
        <div className="text-heading-sm font-bold text-text-heading">
          {t('agents.memory')}
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-white hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          {t('agents.memory.add')}
        </button>
      </div>

      {/* Search & Filters */}
      <div className="mb-6 flex gap-4 px-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-label" />
          <input
            type="text"
            placeholder={t('agents.memory.search-placeholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-border bg-surface-secondary pl-10 pr-4 py-2 text-text-body focus:border-primary focus:outline-none"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as MemoryType | '')}
          className="rounded-lg border border-border bg-surface-secondary px-4 py-2 text-text-body"
        >
          <option value="">{t('agents.memory.filter-all')}</option>
          {(['fact', 'preference', 'context', 'learned'] as MemoryType[]).map((type) => (
            <option key={type} value={type}>
              {t(MEMORY_TYPE_LABELS[type])}
            </option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mb-4 rounded-lg bg-red-100 p-4 text-red-700 dark:bg-red-900 dark:text-red-300">
          {error}
          <button onClick={clearError} className="ml-2 underline">
            {t('common.dismiss')}
          </button>
        </div>
      )}

      {/* Loading */}
      {(loading || searchLoading) && (
        <div className="flex justify-center py-8">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      )}

      {/* Memory List */}
      <div className="flex-1 overflow-auto px-6">
        <div className="grid gap-4 pb-6">
          {displayMemories.map((memory) => (
            <div
              key={memory.id}
              className="rounded-xl border border-border bg-surface-secondary p-4"
            >
              <div className="mb-2 flex items-center justify-between">
                <span className={`rounded-full px-2 py-1 text-xs font-medium ${MEMORY_TYPE_COLORS[memory.memory_type]}`}>
                  {t(MEMORY_TYPE_LABELS[memory.memory_type])}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setEditingMemory(memory)}
                    className="rounded p-1 hover:bg-surface"
                  >
                    <Edit2 className="h-4 w-4 text-text-label" />
                  </button>
                  <button
                    onClick={() => handleDelete(memory.id)}
                    className="rounded p-1 hover:bg-surface"
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </button>
                </div>
              </div>
              <p className="text-text-body">{memory.content}</p>
              <div className="mt-2 flex items-center gap-4 text-xs text-text-label">
                <span>
                  {t('agents.memory.importance')}: {Math.round(memory.importance * 100)}%
                </span>
                <span>
                  {new Date(memory.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
          {displayMemories.length === 0 && !loading && (
            <div className="py-8 text-center text-text-label">
              {t('agents.memory.empty')}
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <MemoryModal
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreate}
        />
      )}

      {/* Edit Modal */}
      {editingMemory && (
        <MemoryModal
          memory={editingMemory}
          onClose={() => setEditingMemory(null)}
          onSave={handleUpdate}
        />
      )}
    </div>
  );
}

// Modal Component
function MemoryModal({
  memory,
  onClose,
  onSave,
}: {
  memory?: AgentMemory;
  onClose: () => void;
  onSave: (data: { content: string; memory_type: MemoryType; importance: number }) => void;
}) {
  const { t } = useTranslation();
  const [content, setContent] = useState(memory?.content || '');
  const [memoryType, setMemoryType] = useState<MemoryType>(memory?.memory_type || 'context');
  const [importance, setImportance] = useState(memory?.importance || 0.5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ content, memory_type: memoryType, importance });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl bg-surface p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-text-heading">
            {memory ? t('agents.memory.edit') : t('agents.memory.create')}
          </h3>
          <button onClick={onClose} className="rounded p-1 hover:bg-surface-secondary">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-text-body">
              {t('agents.memory.content')}
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-border bg-surface-secondary p-3 text-text-body focus:border-primary focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-body">
              {t('agents.memory.type')}
            </label>
            <select
              value={memoryType}
              onChange={(e) => setMemoryType(e.target.value as MemoryType)}
              className="w-full rounded-lg border border-border bg-surface-secondary p-2 text-text-body"
            >
              {(['fact', 'preference', 'context', 'learned'] as MemoryType[]).map((type) => (
                <option key={type} value={type}>
                  {t(MEMORY_TYPE_LABELS[type])}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-body">
              {t('agents.memory.importance')}: {Math.round(importance * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={importance}
              onChange={(e) => setImportance(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-border px-4 py-2 text-text-body hover:bg-surface-secondary"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="rounded-lg bg-primary px-4 py-2 text-white hover:bg-primary/90"
            >
              {t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

**Step 2: Add translations**

In your i18n files, add these keys:
```json
{
  "agents": {
    "memory": {
      "add": "Add Memory",
      "search-placeholder": "Search memories...",
      "filter-all": "All types",
      "confirm-delete": "Are you sure you want to delete this memory?",
      "empty": "No memories yet. Add your first memory!",
      "create": "Create Memory",
      "edit": "Edit Memory",
      "content": "Content",
      "type": "Type",
      "importance": "Importance",
      "types": {
        "fact": "Fact",
        "preference": "Preference",
        "context": "Context",
        "learned": "Learned"
      }
    }
  }
}
```

**Step 3: Commit**

---

## Fase 4: Integração com Agentes

### Task 10: Create Memory Toolkit for Agents

**Files:**
- Create: `backend/app/agent/toolkit/memory_toolkit.py`

**Step 1: Write the toolkit**

```python
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
import logging
from typing import Any

from camel.toolkits.function_tool import FunctionTool

from app.agent.toolkit.abstract_toolkit import AbstractToolkit
from app.model.memory import MemoryCreate, MemorySearchParams, MemoryType
from app.service.memory_service import memory_service

logger = logging.getLogger("memory_toolkit")


class MemoryToolkit(AbstractToolkit):
    """Toolkit for agents to interact with memory

    Provides tools for saving, searching, and managing agent memories.
    """

    agent_name: str = "memory_agent"

    def __init__(self, agent_id: str):
        """Initialize memory toolkit for a specific agent

        Args:
            agent_id: The ID of the agent this toolkit is for
        """
        self.agent_id = agent_id
        self._register_functions()

    def _register_functions(self):
        """Register memory functions as tools"""
        self.functions: list[FunctionTool] = [
            FunctionTool(self.save_memory),
            FunctionTool(self.search_memories),
            FunctionTool(self.list_memories),
            FunctionTool(self.delete_memory),
        ]

    async def save_memory(
        self,
        content: str,
        memory_type: str = "context",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Save a memory for the agent

        Args:
            content: The memory content to save
            memory_type: Type of memory (fact, preference, context, learned)
            importance: Importance level 0-1
            metadata: Additional metadata

        Returns:
            Confirmation message with memory ID
        """
        try:
            memory_type_enum = MemoryType(memory_type)
        except ValueError:
            return f"Invalid memory_type: {memory_type}. Must be one of: fact, preference, context, learned"

        memory = await memory_service.create_memory(
            self.agent_id,
            MemoryCreate(
                content=content,
                memory_type=memory_type_enum,
                importance=importance,
                metadata=metadata or {},
            )
        )

        return f"Memory saved with ID: {memory.id}"

    async def search_memories(
        self,
        query: str,
        limit: int = 5,
        memory_type: str | None = None,
        min_importance: float = 0.0,
    ) -> str:
        """Search memories using natural language query

        Args:
            query: Natural language search query
            limit: Maximum number of results
            memory_type: Filter by memory type (optional)
            min_importance: Minimum importance threshold

        Returns:
            Formatted search results
        """
        memory_type_enum = None
        if memory_type:
            try:
                memory_type_enum = MemoryType(memory_type)
            except ValueError:
                return f"Invalid memory_type: {memory_type}"

        params = MemorySearchParams(
            query=query,
            limit=limit,
            memory_type=memory_type_enum,
            min_importance=min_importance,
        )

        results = await memory_service.search(self.agent_id, params)

        if not results:
            return "No memories found matching your query."

        output = [f"Found {len(results)} relevant memories:\n"]
        for i, result in enumerate(results, 1):
            mem = result.memory
            output.append(
                f"{i}. [{mem.memory_type.value}] (importance: {mem.importance:.0%}) "
                f"[source: {result.source}]\n"
                f"   {mem.content}\n"
            )

        return "\n".join(output)

    async def list_memories(
        self,
        memory_type: str | None = None,
        limit: int = 20,
    ) -> str:
        """List all memories for the agent

        Args:
            memory_type: Filter by memory type (optional)
            limit: Maximum number of results

        Returns:
            Formatted list of memories
        """
        memory_type_enum = None
        if memory_type:
            try:
                memory_type_enum = MemoryType(memory_type)
            except ValueError:
                return f"Invalid memory_type: {memory_type}"

        memories = await memory_service.list_memories(
            self.agent_id, memory_type_enum, limit
        )

        if not memories:
            return "No memories found."

        output = [f"Total memories: {len(memories)}\n"]
        for i, mem in enumerate(memories, 1):
            output.append(
                f"{i}. [{mem.memory_type.value}] (importance: {mem.importance:.0%})\n"
                f"   {mem.content[:100]}{'...' if len(mem.content) > 100 else ''}\n"
            )

        return "\n".join(output)

    async def delete_memory(self, memory_id: str) -> str:
        """Delete a specific memory

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            Confirmation message
        """
        import uuid

        try:
            uuid_obj = uuid.UUID(memory_id)
        except ValueError:
            return f"Invalid memory_id format: {memory_id}"

        await memory_service.delete_memory(self.agent_id, uuid_obj)
        return f"Memory {memory_id} deleted successfully"
```

**Step 2: Commit**

---

### Task 11: Context Injection Helper

**Files:**
- Modify: `backend/app/service/memory_service.py`

**Step 1: Add context injection method**

```python
async def get_context_for_agent(
    self,
    agent_id: str,
    task: str,
    max_memories: int = 5
) -> str:
    """Get relevant context for an agent task

    This can be called before running an agent task to inject
    relevant memories into the system prompt.

    Args:
        agent_id: Agent ID
        task: Current task description
        max_memories: Maximum number of memories to retrieve

    Returns:
        Formatted context string for injection into prompt
    """
    params = MemorySearchParams(
        query=task,
        limit=max_memories,
        min_importance=0.3  # Only relevant memories
    )

    results = await self.search(agent_id, params)

    if not results:
        return ""

    context_parts = ["## Relevant Context from Memory\n"]
    for result in results:
        mem = result.memory
        context_parts.append(
            f"- **{mem.memory_type.value}**: {mem.content}"
        )

    return "\n".join(context_parts)
```

**Step 2: Commit**

---

## Resumo do Plano

| Task | Descrição | Arquivos |
|------|-----------|----------|
| 1 | MemoryType Enum | `backend/app/model/enums.py` |
| 2 | Memory Models | `backend/app/model/memory.py` |
| 3 | Memory Service (CRUD + Qdrant) | `backend/app/service/memory_service.py` |
| 4 | Memory Controller (REST) | `backend/app/controller/memory_controller.py` |
| 5 | BM25 Dependency | `backend/pyproject.toml` |
| 6 | BM25 Search | `backend/app/service/memory_service.py` |
| 7 | Hybrid Search (RRF) | `backend/app/service/memory_service.py` |
| 8 | Memory Store (Zustand) | `src/store/memoryStore.ts` |
| 9 | Memory UI | `src/pages/Agents/Memory.tsx` |
| 10 | Memory Toolkit | `backend/app/agent/toolkit/memory_toolkit.py` |
| 11 | Context Injection | `backend/app/service/memory_service.py` |

---

## Próximos Passos

Após completar a implementação:
1. Testar endpoints com curl/Postman
2. Testar UI manualmente
3. Integrar toolkit nos agentes existentes
4. Adicionar testes unitários

---

**Plan complete and saved to `docs/plans/2026-03-07-memory-module-implementation.md`**

---

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
