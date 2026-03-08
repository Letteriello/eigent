# Memory Consolidation Analysis

> **Analysis Date:** 2026-03-08
> **Author:** Backend Developer Agent

---

## 1. Current Implementation Analysis

### 1.1 What's Already Implemented

**Location:** `backend/app/service/memory_service.py`

| Feature                               | Status   | Location      |
| ------------------------------------- | -------- | ------------- |
| CRUD operations                       | Complete | Lines 114-290 |
| Hybrid search (vector + BM25 + RRF)   | Complete | Lines 325-512 |
| Basic stats                           | Complete | Lines 514-535 |
| MD5-based ID generation (exact dedup) | Complete | Line 98       |

### 1.2 Current Architecture

```
MemoryService
├── _memories: dict (in-memory BM25 index)
├── QdrantStorage (vector embeddings)
├── create_memory() / get_memory() / update_memory() / delete_memory()
├── list_memories()
├── search_memories() → _vector_search() + _bm25_search() + _reciprocal_rank_fusion()
└── get_stats()
```

### 1.3 Current Gaps (vs Research Document)

| Feature                 | Research Spec              | Current State    | Gap    |
| ----------------------- | -------------------------- | ---------------- | ------ |
| Semantic deduplication  | `merge_similar_memories()` | Not implemented  | HIGH   |
| Stale memory cleanup    | `cleanup_stale_memories()` | Not implemented  | HIGH   |
| Contradiction detection | `detect_contradictions()`  | Not implemented  | MEDIUM |
| Scheduled cleanup       | APScheduler jobs           | Not implemented  | MEDIUM |
| API endpoints           | 5 new endpoints            | Not implemented  | HIGH   |
| Metrics tracking        | ConsolidationMetrics       | Basic stats only | MEDIUM |
| Archive functionality   | `_archive_memory()`        | Not implemented  | LOW    |

---

## 2. Gaps Identified

### 2.1 Deduplication Logic (HIGH Priority)

**Current State:**

- MD5 hash generates memory IDs (line 98) - prevents exact duplicate INSERTION
- No semantic similarity checking at creation time
- No merging logic

**What's Missing:**

```python
# Need to add:
async def merge_similar_memories(
    self,
    similarity_threshold: float = 0.9,
    agent_id: str | None = None
) -> ConsolidationResult
```

**Implementation Requirements:**

1. Compute cosine similarity between all memory pairs (O(n²) - needs optimization)
2. Use existing `_get_embedding_model()` for vectors
3. Merge logic: keep higher importance, combine content, update timestamp
4. Delete lower-importance memory from both in-memory dict and Qdrant

### 2.2 Cleanup Scheduler (MEDIUM Priority)

**Current State:**

- No scheduler
- Cleanup only runs when manually triggered

**What's Missing:**

```python
# Need to add:
from apscheduler.schedulers.asyncio import AsyncIOScheduler

def setup_memory_cleanup_scheduler():
    scheduler = AsyncIOScheduler()
    # Daily deduplication at 3am
    scheduler.add_job(run_deduplication, "cron", hour=3, minute=0)
    # Weekly cleanup on Sunday
    scheduler.add_job(run_full_cleanup, "cron", day_of_week="sun", hour=4)
```

**Considerations:**

- APScheduler already used elsewhere in codebase?
- Need to check `pyproject.toml` for dependencies

### 2.3 API Endpoints for Manual Cleanup (HIGH Priority)

**Current State:**

- Only basic CRUD endpoints exist

**What's Missing:**

| Method | Endpoint                                 | Purpose                    |
| ------ | ---------------------------------------- | -------------------------- |
| POST   | `/api/memory/consolidate/merge`          | Run semantic deduplication |
| POST   | `/api/memory/consolidate/cleanup`        | Run stale memory cleanup   |
| GET    | `/api/memory/consolidate/contradictions` | List potential conflicts   |
| POST   | `/api/memory/consolidate/resolve`        | Resolve a conflict         |
| GET    | `/api/memory/consolidation-metrics`      | Get analytics              |

**Files to Modify:**

- `backend/app/controller/memory_controller.py` - Add endpoints
- `backend/app/model/memory.py` - Add request/response models

### 2.4 Metrics Tracking (MEDIUM Priority)

**Current State:**

- `get_stats()` returns basic counts (total, by_type, by_agent)

**What's Missing:**

- Storage size tracking
- Last cleanup timestamp
- Potential merges count
- Stale memories count
- Retrieval quality metrics

**New Response Model Needed:**

```python
class ConsolidationMetrics(BaseModel):
    total_memories: int
    potential_merges: int
    stale_memories: int
    potential_contradictions: int
    storage_bytes: int
    last_cleanup: datetime | None
```

---

## 3. Specific Code Changes Needed

### 3.1 memory_service.py Additions

```python
# NEW METHODS TO ADD (after line 535):

async def merge_similar_memories(
    self,
    similarity_threshold: float = 0.9,
    agent_id: str | None = None
) -> ConsolidationResult:
    """Merge semantically similar memories."""
    pass

async def cleanup_stale_memories(
    self,
    max_age_days: int = 30,
    min_importance: float = 0.5
) -> ConsolidationResult:
    """Remove outdated/low-importance memories."""
    pass

async def detect_contradictions(
    self,
    agent_id: str | None = None
) -> list[Contradiction]:
    """Find potentially contradictory memories."""
    pass

async def get_consolidation_metrics(
    self,
    agent_id: str | None = None
) -> ConsolidationMetrics:
    """Get metrics about memory consolidation needs."""
    pass
```

### 3.2 memory.py Model Additions

```python
# NEW MODELS TO ADD in backend/app/model/memory.py:

class ConsolidationRequest(BaseModel):
    similarity_threshold: float = 0.9
    max_age_days: int = 30
    min_importance: float = 0.5
    agent_id: str | None = None

class ConsolidationResult(BaseModel):
    operation: str
    memories_processed: int
    memories_merged: int
    memories_deleted: int
    memories_archived: int
    duration_ms: float

class Contradiction(BaseModel):
    memory_a: MemoryResponse
    memory_b: MemoryResponse
    similarity: float
    contradiction_type: str | None

class ConsolidationMetrics(BaseModel):
    total_memories: int
    potential_merges: int
    stale_memories: int
    potential_contradictions: int
    storage_bytes: int
    last_cleanup: datetime | None
```

### 3.3 memory_controller.py Endpoints

```python
# NEW ENDPOINTS to add in memory_controller.py:

@router.post("/consolidate/merge")
async def consolidate_merge(request: ConsolidationRequest):
    """Run similarity-based memory merging."""
    pass

@router.post("/consolidate/cleanup")
async def consolidate_cleanup(request: ConsolidationRequest):
    """Run stale memory cleanup."""
    pass

@router.get("/consolidate/contradictions")
async def get_contradictions(agent_id: str | None = None):
    """List potential contradictions."""
    pass

@router.post("/consolidate/resolve")
async def resolve_contradiction(
    memory_id_a: str,
    memory_id_b: str,
    resolution: str  # "keep_a", "keep_b", "merge"
):
    """Resolve a contradiction."""
    pass

@router.get("/consolidation-metrics")
async def get_consolidation_metrics(agent_id: str | None = None):
    """Get consolidation analytics."""
    pass
```

---

## 4. Priority Order

### Phase 1: Core Consolidation (Week 1)

1. **Add merge_similar_memories()** - semantic deduplication
2. **Add cleanup_stale_memories()** - TTL-based cleanup
3. **Create API endpoints** - manual trigger endpoints
4. **Add request/response models**

**Rationale:** These provide immediate value - reduces storage, improves retrieval quality

### Phase 2: Metrics & Monitoring (Week 2)

5. **Extend get_stats()** → `get_consolidation_metrics()`
6. **Add storage size tracking**
7. **Add last_cleanup timestamp**

**Rationale:** Need metrics to know when cleanup is needed

### Phase 3: Advanced Features (Week 3)

8. **Implement contradiction detection**
9. **Add APScheduler integration**
10. **Implement trigger-based cleanup** (on memory count threshold)

**Rationale:** Advanced features - lower immediate ROI

### Phase 4: Optimization (Week 4)

11. **Optimize similarity computation** (faiss instead of O(n²))
12. **Batch processing for large datasets**
13. **Add frontend UI for manual controls**

**Rationale:** Performance and UX polish

---

## 5. Dependencies to Check

```bash
# Check if these are in pyproject.toml:
uv add apscheduler      # For scheduled cleanup
uv add rank_bm25        # Already used in BM25 search
```

---

## 6. Key Implementation Notes

### Deduplication Algorithm

1. Get all memories (use `list_memories()`)
2. Compute pairwise similarities (O(n²) for now)
3. For pairs with similarity > threshold:
   - Keep higher importance memory
   - Merge content: "Current: {newer}. Previously: {older}."
   - Update timestamp to most recent
   - Delete lower importance memory
4. Return ConsolidationResult with counts

### Cleanup Algorithm

1. Iterate through all memories
2. Calculate age = now - updated_at
3. If importance < min_importance AND age > 7 days → delete
4. If age > max_age_days → archive (or delete)
5. Track last_cleanup timestamp

### Qdrant Delete Issue

Current `delete_memory()` doesn't actually delete from Qdrant (line 287-290 comment). This needs fixing before consolidation can properly work.

---

## 7. Files to Modify

| File                                          | Changes                   |
| --------------------------------------------- | ------------------------- |
| `backend/app/service/memory_service.py`       | Add 4 new methods         |
| `backend/app/model/memory.py`                 | Add 4 new Pydantic models |
| `backend/app/controller/memory_controller.py` | Add 5 new endpoints       |
| `pyproject.toml`                              | Add apscheduler if needed |

---

## 8. Testing Strategy

1. Unit tests for `merge_similar_memories()`
2. Unit tests for `cleanup_stale_memories()`
3. Integration tests for API endpoints
4. Manual test: create 10 memories, run merge, verify deduplication
