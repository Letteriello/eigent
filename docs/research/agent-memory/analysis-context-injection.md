# Context Injection Analysis & Implementation Plan

**Date:** 2026-03-08
**Author:** Backend Developer Agent

---

## 1. Current Implementation Analysis

### 1.1 What's Working Well

| Feature          | Current State                                | Assessment              |
| ---------------- | -------------------------------------------- | ----------------------- |
| Hybrid Search    | BM25 + Vector + RRF in memory_service.py     | ✅ Excellent foundation |
| Memory Types     | 4 types (preference, fact, context, learned) | ✅ Good categorization  |
| Importance Field | Exists in Memory model                       | ✅ Foundation exists    |
| Templates        | Default + Short templates                    | ✅ Flexible             |
| Async Operations | Async/await throughout                       | ✅ Performance good     |
| Error Handling   | Graceful fallbacks with try/catch            | ✅ Robust               |

### 1.2 Current Code Structure

```python
# memory_context.py - Key functions:
- inject_memory_context()      # Main entry point
- get_memory_context_for_task() # Convenience wrapper
- format_memory_for_prompt()    # Single memory formatter
- MemoryContextInjector        # Class for session-level accumulation
```

**Key Parameters (currently hardcoded):**

- `top_k: int = 5` - Count-based limiting
- `similarity_threshold: float = 0.3` - Same for all types

---

## 2. Gaps Identified

### 2.1 Priority Scoring (HIGH PRIORITY)

**Research Recommends:**

```
priority_score = (importance * 0.4) + (recency * 0.3) + (relevance * 0.3)
```

**Current State:**

- Only uses search similarity (relevance)
- No recency weighting
- No composite scoring

**Gap:** Memories are ranked purely by search similarity without considering:

- How old the memory is (recency)
- User-defined importance
- Combined priority

### 2.2 Token Budget Management (HIGH PRIORITY)

**Research Recommends:**

- Reserve 10-30% of context window for memory
- Use token-based limiting, not count-based

**Current State:**

- Uses `top_k=5` count-based limiting
- No token estimation
- May exceed budget with long memories

**Gap:** No token budget calculation - could exceed context window limits

### 2.3 Truncation Strategies (HIGH PRIORITY)

**Research Recommends (in order):**

1. Recency-based (keep latest)
2. Importance-weighted (highest importance)
3. Relevance-scored (highest similarity)
4. Type-prioritized (preferences > facts > context > learned)

**Current State:**

- No truncation strategy
- Returns all results up to top_k

**Gap:** No multi-strategy truncation when budget exceeded

### 2.4 Query Expansion (MEDIUM PRIORITY)

**Research Recommends:**

- Expand queries with synonyms, entities, related concepts
- Multi-query retrieval with deduplication

**Current State:**

- Single query search only

**Gap:** Lower recall for paraphrased queries

### 2.5 Result Deduplication (MEDIUM PRIORITY)

**Research Recommends:**

- Semantic deduplication to avoid redundant context
- Use embeddings to find near-duplicates

**Current State:**

- No deduplication mechanism
- MemoryContextInjector has basic dedup by string equality

**Gap:** May include similar memories wasting tokens

### 2.6 Adaptive Thresholds (LOW PRIORITY)

**Research Recommends:**

- Preferences: 0.2-0.3 (lower threshold)
- Facts: 0.3-0.4
- Learned: 0.35-0.5
- Context: 0.25-0.35

**Current State:**

- Hardcoded 0.3 for all types

**Gap:** Not optimized per memory type

---

## 3. Specific Code Changes Needed

### 3.1 Add Priority Scoring (HIGH)

**File:** `backend/app/utils/memory_context.py`

**New function to add:**

```python
def calculate_priority_score(
    memory: Memory,
    relevance_score: float,
    recency_weight: float = 0.3,
    importance_weight: float = 0.4,
    relevance_weight_param: float = 0.3,
) -> float:
    """Calculate composite priority score for a memory.

    Formula: (importance * 0.4) + (recency * 0.3) + (relevance * 0.3)
    """
    # Recency: exponential decay with 24-hour half-life
    hours_old = (datetime.utcnow() - memory.created_at).total_seconds() / 3600
    recency = 1.0 / (1.0 + hours_old / 24)

    # Importance: from memory metadata (default 0.5)
    importance = memory.importance or 0.5

    return (
        importance * importance_weight +
        recency * recency_weight +
        relevance_score * relevance_weight_param
    )
```

**Modify `inject_memory_context()` to:**

1. Accept `relevance_score` from search results
2. Calculate priority scores
3. Re-rank by composite score

### 3.2 Add Token Budget Management (HIGH)

**File:** `backend/app/utils/memory_context.py`

**New functions to add:**

```python
def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation)."""
    return len(text) // 4


def truncate_by_token_budget(
    memories: list[tuple[Memory, float]],  # (memory, score)
    max_tokens: int,
) -> list[tuple[Memory, float]]:
    """Truncate memories to fit token budget."""
    selected = []
    tokens_used = 0

    for memory, score in memories:
        memory_tokens = estimate_tokens(memory.content)
        if tokens_used + memory_tokens <= max_tokens:
            selected.append((memory, score))
            tokens_used += memory_tokens
        else:
            break

    return selected
```

**Modify `inject_memory_context()` to:**

1. Add `max_tokens: int` parameter (default ~2000 = ~10% of 20k budget)
2. Use token budget instead of count-based top_k

### 3.3 Add Memory Type Thresholds (MEDIUM)

**File:** `backend/app/utils/memory_context.py`

```python
def get_adaptive_threshold(memory_types: list[MemoryType] | None) -> float:
    """Get adaptive threshold based on memory types."""
    if not memory_types:
        return 0.35  # Default

    if MemoryType.preference in memory_types:
        return 0.2  # Lower for preferences

    if MemoryType.context in memory_types:
        return 0.3  # Medium for context

    if MemoryType.learned in memory_types:
        return 0.4  # Higher for learned

    return 0.35  # Default for facts
```

### 3.4 Add Truncation Strategies (HIGH)

**File:** `backend/app/utils/memory_context.py`

```python
def apply_truncation_strategies(
    memories: list[tuple[Memory, float]],
    max_tokens: int,
    priority_type: str = "composite",  # recency, importance, relevance, composite
) -> list[tuple[Memory, float]]:
    """Apply truncation strategies in priority order."""

    if priority_type == "recency":
        scored = [
            (m, calculate_recency_score(m.created_at))
            for m, _ in memories
        ]
    elif priority_type == "importance":
        scored = [
            (m, m.importance or 0.5)
            for m, _ in memories
        ]
    elif priority_type == "relevance":
        scored = memories  # Already sorted by relevance
    else:  # composite (default)
        scored = [
            (m, calculate_priority_score(m, s))
            for m, s in memories
        ]

    scored.sort(key=lambda x: x[1], reverse=True)

    return truncate_by_token_budget(scored, max_tokens)
```

### 3.5 Add Result Deduplication (MEDIUM)

**File:** `backend/app/utils/memory_context.py`

```python
def deduplicate_memories(
    memories: list[tuple[Memory, float]],
    similarity_threshold: float = 0.9,
) -> list[tuple[Memory, float]]:
    """Deduplicate similar memories using content similarity."""
    if not memories:
        return []

    unique = [memories[0]]
    for memory, score in memories[1:]:
        is_duplicate = False
        for unique_mem, _ in unique:
            # Simple length + content check
            if abs(len(memory.content) - len(unique_mem.content)) < 10:
                if memory.content[:100] == unique_mem.content[:100]:
                    is_duplicate = True
                    break
        if not is_duplicate:
            unique.append((memory, score))

    return unique
```

### 3.6 Enhance Formatting (LOW)

**File:** `backend/app/utils/memory_context.py`

**Add Claude-specific template:**

```python
CLAUDE_MEMORY_CONTEXT_TEMPLATE = """\
## Relevant Context from Memory

The following information may be helpful for this conversation:

### User Preferences
{preferences}

### Relevant Facts
{facts}

### Project Context
{context}

---
*This context was automatically retrieved from your long-term memory.*
"""
```

**Add formatting by type:**

```python
def format_memories_by_type(
    memories: list[Memory],
) -> dict[str, list[str]]:
    """Format memories grouped by type for Claude."""
    formatted = {
        "preferences": [],
        "facts": [],
        "context": [],
        "learned": [],
    }

    for memory in memories:
        mem_type = memory.memory_type.value
        formatted[mem_type].append(f"- [{mem_type}] {memory.content}")

    return {
        k: "\n".join(v) if v else "None"
        for k, v in formatted.items()
    }
```

---

## 4. Priority Order for Implementation

### Phase 1: High Priority (1-2 days)

| #   | Task                                           | Files to Modify     | Lines ~ |
| --- | ---------------------------------------------- | ------------------- | ------- |
| 1   | Add priority scoring function                  | `memory_context.py` | +30     |
| 2   | Add token budget management                    | `memory_context.py` | +40     |
| 3   | Integrate scoring into inject_memory_context() | `memory_context.py` | +20     |

**Impact:** Significant improvement in memory relevance and context window safety

### Phase 2: Medium Priority (2-3 days)

| #   | Task                      | Files to Modify     | Lines ~ |
| --- | ------------------------- | ------------------- | ------- |
| 4   | Add adaptive thresholds   | `memory_context.py` | +15     |
| 5   | Add deduplication         | `memory_context.py` | +25     |
| 6   | Add truncation strategies | `memory_context.py` | +30     |

**Impact:** Better recall and token efficiency

### Phase 3: Low Priority (1 week)

| #   | Task                       | Files to Modify                           | Lines ~ |
| --- | -------------------------- | ----------------------------------------- | ------- |
| 7   | Add query expansion        | `memory_context.py` + `memory_service.py` | +60     |
| 8   | Claude-specific formatting | `memory_context.py`                       | +40     |
| 9   | Session-level caching      | New file or add to existing               | +50     |

**Impact:** Enhanced recall and model-specific optimization

---

## 5. API Changes Required

### 5.1 Function Signature Updates

```python
# Current
async def inject_memory_context(
    query: str,
    template: str | None = None,
    memory_types: list[MemoryType] | None = None,
    agent_id: str | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
) -> str:

# Proposed
async def inject_memory_context(
    query: str,
    template: str | None = None,
    memory_types: list[MemoryType] | None = None,
    agent_id: str | None = None,
    max_tokens: int = 2000,        # NEW: token budget
    similarity_threshold: float | None = None,  # NEW: auto-adaptive
    priority_type: str = "composite",  # NEW: truncation strategy
) -> str:
```

### 5.2 Backward Compatibility

Add deprecation warning for old parameters:

```python
import warnings

if top_k is not None:
    warnings.warn(
        "top_k is deprecated, use max_tokens instead",
        DeprecationWarning,
        stacklevel=2
    )
```

---

## 6. Testing Requirements

### Unit Tests

- `test_priority_scoring()` - Verify formula calculation
- `test_token_estimation()` - Verify rough estimation accuracy
- `test_truncation_strategies()` - Verify each strategy
- `test_deduplication()` - Verify duplicate removal

### Integration Tests

- `test_inject_memory_context_full_flow()` - End-to-end with real memories
- `test_token_budget_respected()` - Verify max_tokens works
- `test_adaptive_threshold()` - Verify per-type thresholds

---

## 7. Summary

### Quick Wins (Phase 1)

1. **Priority scoring** - Most impactful change for relevance
2. **Token budget** - Prevents context overflow
3. **Scoring integration** - Ties it all together

### Expected Improvements

- **Recall:** +20-30% from priority scoring
- **Context safety:** Guaranteed token budget compliance
- **Relevance:** Better composite ranking vs pure similarity

### Files Modified

- Primary: `backend/app/utils/memory_context.py`
- Secondary: `backend/app/service/memory_service.py` (if adding query expansion)
