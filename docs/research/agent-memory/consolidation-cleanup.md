# Agent Memory Consolidation and Cleanup Strategies

> **Research Date:** 2026-03-08
> **Status:** Research Document - Implementation Ready

This document covers strategies for consolidating and cleaning up agent memories in the Eigent AI Desktop system.

---

## 1. Why Consolidate Memories

### 1.1 Storage Efficiency

As agents accumulate memories over time, storage costs grow linearly with memory count. Without consolidation:

- **Redundant storage**: Duplicate or near-duplicate memories waste vector DB space
- **Index bloat**: Larger indexes mean slower search queries
- **Increased API costs**: More embeddings = higher embedding API costs

**Current State in Eigent:**
- MemoryService stores in-memory dict + Qdrant vector DB
- No deduplication on memory creation
- Each memory generates a new embedding vector

### 1.2 Retrieval Quality

Memory retrieval degrades when:
- **Signal-to-noise ratio drops**: Low-importance memories dilute relevant results
- **Contradictory information**: Conflicting memories confuse the agent
- **Stale data**: Outdated information may be retrieved instead of current facts

**Impact on Hybrid Search:**
- RRF combines vector + BM25 results
- More memories = more noise in top-k results
- Importance scores (0-1) exist but aren't used in retrieval weighting

### 1.3 Deduplication

Memory deduplication identifies and merges:
- **Exact duplicates**: Same content hash
- **Semantic duplicates**: High cosine similarity (>0.95) with different wording
- **Subset memories**: One memory completely contains another

**Current Deduplication:**
- MD5 hash generates memory IDs (prevents exact duplicates at creation)
- No semantic deduplication implemented

---

## 2. Consolidation Strategies

### 2.1 Merging Similar Memories

**Approach:** When two memories have high semantic similarity, merge them into one.

**Implementation Algorithm:**

```
1. For each memory pair with cosine similarity > threshold (0.9):
   a. Compare importance scores
   b. Keep the higher-importance memory
   c. Merge content: "Current: {newer fact}. Previously: {older fact}."
   d. Update timestamps to most recent
   e. Delete the lower-importance memory
```

**Use Cases:**
- Agent learns the same fact multiple times with different phrasing
- User provides updated context that supersedes previous

**Code Sketch:**
```python
async def merge_similar_memories(
    self, 
    similarity_threshold: float = 0.9
) -> MergeResult:
    """Merge memories with high semantic similarity."""
    merged_count = 0
    
    # Get all memories
    all_memories = await self.list_memories(limit=10000)
    
    # Compare pairs (O(n²) - optimize for large datasets)
    to_merge = []
    for i, mem_a in enumerate(all_memories):
        for mem_b in all_memories[i+1:]:
            sim = await self._compute_similarity(mem_a, mem_b)
            if sim > similarity_threshold:
                to_merge.append((mem_a, mem_b, sim))
    
    # Merge each pair
    for mem_a, mem_b, sim in to_merge:
        await self._perform_merge(mem_a, mem_b)
        merged_count += 1
    
    return MergeResult(merged=merged_count)
```

### 2.2 Updating Outdated Information

**Approach:** Detect and update memories that have been superseded by newer information.

**Strategies:**

1. **Timestamp-based expiration:**
   - Tag memories with TTL or expiration dates
   - Auto-expire session-scoped memories after session ends
   - Mark context memories as stale after N hours

2. **Content freshness detection:**
   - Use LLM to compare two memories and determine if one supersedes another
   - Example: "User's name is John" → "User's name is John Smith"

3. **Importance-based retention:**
   - High importance (0.8-1.0): Keep indefinitely
   - Medium importance (0.4-0.7): Keep for 30 days
   - Low importance (0.0-0.3): Keep for 7 days

**Implementation:**
```python
async def cleanup_stale_memories(
    self, 
    max_age_days: int = 30,
    min_importance: float = 0.5
) -> CleanupResult:
    """Remove or archive stale memories."""
    deleted = []
    
    for memory in self._memories.values():
        age_days = (datetime.utcnow() - memory["updated_at"]).days
        
        if memory["importance"] < min_importance and age_days > 7:
            await self.delete_memory(memory["id"])
            deleted.append(memory["id"])
        elif age_days > max_age_days:
            # Archive instead of delete
            await self._archive_memory(memory["id"])
            deleted.append(memory["id"])
    
    return CleanupResult(deleted_count=len(deleted))
```

### 2.3 Removing Contradictions

**Approach:** Detect and resolve conflicting memories.

**Detection Methods:**

1. **Direct contradiction detection:**
   - Pattern matching: "X is Y" vs "X is not Y"
   - Temporal contradictions: "Meeting at 2pm" vs "Meeting at 3pm"

2. **LLM-based contradiction detection:**
   - Prompt LLM to compare two memories
   - Determine if they contradict or are compatible

**Resolution Strategies:**

| Strategy | When to Use | Action |
|----------|-------------|--------|
| Keep Newer | Temporal conflict | Keep memory with more recent timestamp |
| Keep Higher Importance | Quality conflict | Keep memory with higher importance score |
| Keep Both + Flag | Ambiguous | Mark both for human review |
| Merge Context | Partial overlap | Combine into single comprehensive memory |

---

## 3. Automation Approaches

### 3.1 Scheduled Cleanup

**Option A: Background Task (Celery/APScheduler)**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def setup_memory_cleanup():
    # Daily deduplication at 3am
    scheduler.add_job(
        run_deduplication,
        "cron",
        hour=3,
        minute=0
    )
    # Weekly full cleanup on Sunday
    scheduler.add_job(
        run_full_cleanup,
        "cron",
        day_of_week="sun",
        hour=4,
        minute=0
    )
```

**Option B: On-Demand Cleanup**

Triggered by:
- User action in UI (button click)
- API endpoint call
- Memory count threshold (e.g., >1000 memories)

### 3.2 Trigger-Based Cleanup

**Automatic Triggers:**

| Trigger | Action |
|---------|--------|
| Memory count > 1000 | Run deduplication |
| Search quality < threshold | Run cleanup + reindex |
| Session end | Archive session memories |
| Agent inactivity > 7 days | Age-based cleanup |

**Implementation:**
```python
async def on_memory_created(self, memory: MemoryResponse):
    """Trigger cleanup when memory count threshold hit."""
    stats = await self.get_stats()
    
    if stats.total_memories % 1000 == 0:
        logger.info("Memory threshold reached, running deduplication")
        await self.merge_similar_memories(similarity_threshold=0.85)
```

### 3.3 Manual Cleanup UI

**Frontend Components Needed:**

1. **Memory Dashboard**
   - Total memory count graph over time
   - Storage usage meter
   - Last cleanup timestamp

2. **Cleanup Controls**
   - "Run Deduplication" button
   - "Clean Stale Memories" button
   - Configuration sliders (thresholds)

3. **Memory Browser**
   - List all memories with filters
   - Bulk delete capability
   - Manual merge interface

---

## 4. Metrics to Track

### 4.1 Memory Count Over Time

**Key Metrics:**
- Total memories per agent
- Memories by type (fact, preference, context, learned)
- Daily/weekly memory creation rate

**Implementation:**
```python
class MemoryMetrics:
    async def track_memory_count(self, agent_id: str) -> dict:
        """Track memory count metrics."""
        stats = await get_memory_service().get_stats()
        
        return {
            "total": stats.total_memories,
            "by_type": stats.by_type,
            "by_agent": stats.by_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
```

**Dashboard Visualization:**
```
Memory Count Over Time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 500│                    ┌───┐
    │              ┌───┐ │   │
    │        ┌───┐│   │ │   │
    │  ┌───┐ │   ││   │ │   │
    │  │   │ │   ││   │ │   │
  0 └──┴───┴─┴───┴┴───┴─┴───┴────
      Jan  Feb  Mar  Apr  May  Jun
```

### 4.2 Retrieval Quality

**Metrics:**
- Average similarity score of top-k results
- Relevance rating (if user feedback available)
- Time to retrieve top-k results

**Implementation:**
```python
async def measure_retrieval_quality(
    self, 
    test_queries: list[str]
) -> RetrievalQualityMetrics:
    """Measure retrieval quality metrics."""
    total_relevance = 0.0
    total_time = 0.0
    
    for query in test_queries:
        start = time.time()
        results = await self.search_memories(
            MemorySearchQuery(query=query, top_k=5)
        )
        elapsed = time.time() - start
        
        # Compute average relevance of top results
        # (simplified - would need ground truth for real metrics)
        avg_relevance = sum(
            r.importance for r in results.memories
        ) / len(results.memories) if results.memories else 0
        
        total_relevance += avg_relevance
        total_time += elapsed
    
    return RetrievalQualityMetrics(
        avg_relevance_score=total_relevance / len(test_queries),
        avg_query_time_ms=total_time / len(test_queries) * 1000
    )
```

### 4.3 Storage Usage

**Metrics:**
- Vector DB storage size
- In-memory dict size
- Embedding vector count
- Qdrant collection size

**Implementation:**
```python
async def get_storage_metrics(self) -> StorageMetrics:
    """Get storage usage metrics."""
    storage_path = self._storage_path
    
    # Vector DB size
    db_size = sum(
        f.stat().st_size 
        for f in storage_path.rglob("*") 
        if f.is_file()
    )
    
    # Memory count
    memory_count = len(self._memories)
    
    # Embedding dimension and count
    embedding_count = memory_count  # One per memory
    
    return StorageMetrics(
        vector_db_bytes=db_size,
        memory_count=memory_count,
        embedding_dimension=EMBEDDING_DIM,
        estimated_embedding_storage_mb=(
            embedding_count * EMBEDDING_DIM * 4 / 1_000_000
        )
    )
```

---

## 5. Implementation for Eigent

### 5.1 Service Extensions

**New Methods in MemoryService:**

```python
# In backend/app/service/memory_service.py

class MemoryService:
    # ... existing methods ...
    
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
    
    async def resolve_contradiction(
        self,
        memory_id_a: str,
        memory_id_b: str,
        resolution: Literal["keep_a", "keep_b", "merge"]
    ) -> MemoryResponse:
        """Resolve a contradiction between two memories."""
        pass
    
    async def get_consolidation_metrics(
        self,
        agent_id: str | None = None
    ) -> ConsolidationMetrics:
        """Get metrics about memory consolidation needs."""
        pass
```

### 5.2 API Endpoints Needed

**New Endpoints in memory_controller.py:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/memory/consolidate/merge` | Run similarity-based merging |
| POST | `/api/memory/consolidate/cleanup` | Run stale memory cleanup |
| GET | `/api/memory/consolidate/contradictions` | List potential contradictions |
| POST | `/api/memory/consolidate/resolve` | Resolve a contradiction |
| GET | `/api/memory/consolidation-metrics` | Get consolidation analytics |

**Request/Response Models:**

```python
# Consolidation request/response models

class ConsolidationRequest(BaseModel):
    """Request for consolidation operations."""
    similarity_threshold: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Threshold for merging similar memories"
    )
    max_age_days: int = Field(
        default=30,
        ge=1,
        description="Maximum age in days for cleanup"
    )
    min_importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum importance to preserve"
    )
    agent_id: str | None = None


class ConsolidationResult(BaseModel):
    """Result of consolidation operation."""
    operation: str
    memories_processed: int
    memories_merged: int
    memories_deleted: int
    memories_archived: int
    duration_ms: float


class Contradiction(BaseModel):
    """A pair of potentially contradictory memories."""
    memory_a: MemoryResponse
    memory_b: MemoryResponse
    similarity: float
    contradiction_type: str | None


class ConsolidationMetrics(BaseModel):
    """Metrics about memory consolidation state."""
    total_memories: int
    potential_merges: int
    stale_memories: int
    potential_contradictions: int
    storage_bytes: int
    last_cleanup: datetime | None
```

### 5.3 Frontend Integration

**Store Extension (memoryStore.ts):**

```typescript
interface MemoryConsolidationState {
  // Current metrics
  metrics: ConsolidationMetrics | null;
  
  // Operations
  isConsolidating: boolean;
  lastCleanup: Date | null;
  
  // Actions
  runDeduplication: (threshold?: number) => Promise<void>;
  runCleanup: (maxAgeDays?: number) => Promise<void>;
  fetchMetrics: () => Promise<void>;
  resolveContradiction: (idA: string, idB: string, resolution: string) => Promise<void>;
}
```

**UI Components:**

1. **MemorySettingsPanel**
   - Consolidation toggle
   - Threshold sliders
   - Schedule configuration

2. **MemoryAnalytics**
   - Memory count chart
   - Storage usage gauge
   - Last cleanup indicator

3. **ContradictionResolver**
   - Side-by-side memory comparison
   - Resolution action buttons

---

## 6. Recommended Implementation Plan

### Phase 1: Basic Consolidation (Week 1)
- [ ] Add `merge_similar_memories()` method
- [ ] Add `cleanup_stale_memories()` method
- [ ] Create API endpoints for both
- [ ] Add manual trigger buttons in UI

### Phase 2: Metrics & Monitoring (Week 2)
- [ ] Implement `get_consolidation_metrics()`
- [ ] Add memory count over time tracking
- [ ] Create analytics dashboard in UI
- [ ] Add storage usage display

### Phase 3: Advanced Features (Week 3)
- [ ] Implement contradiction detection
- [ ] Add LLM-based freshness checking
- [ ] Create scheduled cleanup jobs
- [ ] Implement trigger-based cleanup

### Phase 4: Optimization (Week 4)
- [ ] Optimize similarity computation (faiss index)
- [ ] Add batch processing for large datasets
- [ ] Implement incremental cleanup (not full scan)
- [ ] Add user feedback loop for quality

---

## 7. Open Questions

1. **Similarity threshold tuning**: What threshold works best? Start with 0.9, adjust based on user feedback.

2. **LLM usage for contradictions**: Should we use LLM for contradiction detection? Adds cost but more accurate.

3. **Archive vs delete**: Should stale memories be archived instead of deleted? Yes, for audit trail.

4. **Agent-specific vs global cleanup**: Should consolidation run per-agent or globally? Per-agent allows more control.

5. **User control vs automation**: How much should be automatic vs user-controlled? Start with manual, add automation gradually.

---

## Appendix A: Current Memory Types

From `backend/app/model/enums.py`:

```python
class MemoryType(str, Enum):
    fact = "fact"           # Factual information
    preference = "preference"  # User preferences
    context = "context"     # Conversation context
    learned = "learned"     # Learned patterns
```

---

## Appendix B: Related Files

| File | Purpose |
|------|---------|
| `backend/app/service/memory_service.py` | Core memory service |
| `backend/app/controller/memory_controller.py` | API endpoints |
| `backend/app/model/memory.py` | Pydantic models |
| `backend/app/model/enums.py` | MemoryType enum |
| `backend/app/agent/toolkit/memory_toolkit.py` | Agent tool integration |
| `src/store/memoryStore.ts` | Frontend store |
| `src/pages/Agents/Memory.tsx` | Memory UI page |
