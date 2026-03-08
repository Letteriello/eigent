# Context Injection Patterns for AI Agent Prompts

**Date:** 2026-03-08
**Status:** Research Complete
**Author:** Claude Code

---

## 1. Context Window Management

### 1.1 How Much Memory Context to Include

Context window limits vary significantly across models:

| Model | Context Window | Recommended Memory Allocation |
|-------|----------------|-------------------------------|
| Claude 3.5 Sonnet | 200K tokens | 10-30% of window |
| GPT-4 Turbo | 128K tokens | 10-20% of window |
| GPT-4 | 8K-32K tokens | 15-25% of window |
| Claude 3 Haiku | 200K tokens | 15-30% of window |

**Rule of Thumb:** Reserve 50-70% of context for:
- Current conversation history
- System prompt
- Tool definitions and outputs
- Working memory (immediate task context)

**Memory Context Budget:** 10-30% of remaining tokens after other requirements.

### 1.2 Truncation Strategies

When memory context exceeds budget, apply these strategies in order:

```
Priority 1: Recency-based (keep latest)
Priority 2: Importance-weighted (keep highest importance score)
Priority 3: Relevance-scored (keep highest similarity to current query)
Priority 4: Type-prioritized (preferences > facts > context > learned)
```

**Implementation Pattern:**
```python
def truncate_memories(memories: list[Memory], max_tokens: int) -> list[Memory]:
    # Sort by composite score
    scored = [
        (m, calculate_priority_score(m, recency_weight=0.3, importance_weight=0.4, relevance_weight=0.3))
        for m in memories
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Select until token budget exhausted
    selected = []
    tokens_used = 0
    for memory, score in scored:
        memory_tokens = estimate_tokens(memory.content)
        if tokens_used + memory_tokens <= max_tokens:
            selected.append(memory)
            tokens_used += memory_tokens
        else:
            break
    
    return selected
```

### 1.3 Priority Ranking for Memories

**Composite Score Formula:**
```
priority_score = (importance * 0.4) + (recency * 0.3) + (relevance * 0.3)
```

Where:
- **importance**: User-defined or auto-calculated (1.0 = critical, 0.1 = trivial)
- **recency**: Time-based decay (1.0 = now, 0.0 = infinitely old)
- **relevance**: Similarity score from search (0.0-1.0)

---

## 2. Retrieval Strategies

### 2.1 Similarity Threshold Tuning

Default thresholds by memory type:

| Memory Type | Recommended Threshold | Rationale |
|-------------|----------------------|-----------|
| Preferences | 0.2-0.3 | User preferences should rarely be missed |
| Facts | 0.3-0.4 | Factual recall needs precision |
| Learned | 0.35-0.5 | Derived knowledge can be more specific |
| Context | 0.25-0.35 | Broader context is useful |

**Adaptive Threshold:**
```python
def get_adaptive_threshold(memory_types: list[MemoryType]) -> float:
    if MemoryType.preference in memory_types:
        return 0.2  # Lower threshold for preferences
    if MemoryType.context in memory_types:
        return 0.3  # Medium for context
    return 0.35  # Default
```

### 2.2 Query Expansion

Expand user queries to improve recall:

```python
async def expand_query(original_query: str) -> list[str]:
    expansions = [
        original_query,
        # Add synonyms
        await get_synonyms(original_query),
        # Add related concepts
        await get_related_concepts(original_query),
        # Add entity names
        extract_entities(original_query),
    ]
    return [e for e in expansions if e]  # Filter empty
```

**Multi-query Retrieval:**
```python
async def retrieve_with_expansion(query: str, top_k: int) -> list[Memory]:
    expanded_queries = await expand_query(query)
    
    all_results = []
    for expanded_q in expanded_queries:
        results = await search_memories(expanded_q, top_k=top_k)
        all_results.extend(results)
    
    # Deduplicate and re-rank
    return deduplicate_and_rerank(all_results, top_k)
```

### 2.3 Re-ranking Results

After initial retrieval, apply re-ranking:

**Cross-encoder Re-ranking:**
```python
async def rerank_memories(query: str, memories: list[Memory], top_k: int) -> list[Memory]:
    # Use cross-encoder for accurate scoring
    cross_encoder = load_cross_encoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    pairs = [(query, mem.content) for mem in memories]
    scores = cross_encoder.predict(pairs)
    
    # Combine with original relevance
    combined = [
        (mem, original_score * 0.4 + cross_score * 0.6)
        for mem, original_score in zip(memories, get_original_scores(memories))
    ]
    
    combined.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in combined[:top_k]]
```

---

## 3. Formatting for Different Models

### 3.1 Claude-Specific Patterns

Claude responds well to structured, markdown-formatted context:

```markdown
## Relevant Context from Memory

The following information may be helpful for this conversation:

### User Preferences
- [preference] User prefers TypeScript over JavaScript
- [preference] User likes dark mode enabled

### Relevant Facts
- [fact] Current project uses React 18 with TypeScript

### Project Context
- [context] This is a desktop application for AIThis context agents

---
* was automatically retrieved from your long-term memory.*
```

**Claude Optimizations:**
- Use clear section headers
- Prefix memories with type tags
- Include "may be helpful" framing (not absolute)
- Add attribution line for transparency
- Max 5-7 memories per injection

### 3.2 GPT-Specific Patterns

GPT models prefer concise, direct formatting:

```markdown
Relevant context:
- Preference: User prefers Python for data tasks
- Fact: Current backend is FastAPI
- Context: Project is an AI desktop application
```

**GPT Optimizations:**
- Bullet-point format
- Single-line entries when possible
- Less verbose headers
- Direct "Relevant context:" prefix

### 3.3 Token Optimization

**Compression Techniques:**

| Technique | Token Savings | Use When |
|----------|--------------|----------|
| Remove stop words | 20-30% | High memory volume |
| Abbreviate types | 5-10% | Always safe |
| Merge similar | 10-20% | Many related memories |
| Summarize | 30-50% | Long-form memories |

**Implementation:**
```python
def compress_memory_content(content: str, memory_type: MemoryType) -> str:
    if memory_type == MemoryType.preference:
        return content  # Keep preferences verbose
    
    if len(content) > 200:
        # Truncate with ellipsis for non-critical
        return content[:197] + "..."
    
    return content
```

---

## 4. Current Eigent Analysis

### 4.1 What's Working Well

| Feature | Implementation | Assessment |
|---------|---------------|------------|
| **Hybrid Search** | BM25 + Vector + RRF | ✅ Excellent - best practice |
| **Memory Types** | 4 types (preference, fact, context, learned) | ✅ Good categorization |
| **Importance Scoring** | Metadata-based importance field | ✅ Foundation exists |
| **Templates** | Default + Short templates | ✅ Flexible formatting |
| **Async Operations** | Async/await throughout | ✅ Good performance |
| **Error Handling** | Graceful fallbacks | ✅ Robust |

### 4.2 Current Implementation Analysis

**Strengths:**
```python
# Good: Hybrid search with RRF
combined = self._reciprocal_rank_fusion(vector_results, bm25_results, top_k)

# Good: Type-based filtering
if memory_types:
    filtered = [m for m in results if m.memory_type.value in type_values]

# Good: Configurable thresholds
similarity_threshold: float = 0.3
```

**Areas for Improvement:**

1. **No Recency Weighting**
   - Current: Memories are ranked only by search similarity
   - Missing: Time-based decay for recency
   - Impact: Old but relevant memories may not be best fit

2. **No Query Expansion**
   - Current: Single query search
   - Missing: Synonym expansion, entity extraction
   - Impact: Lower recall for paraphrased queries

3. **Hard-coded Parameters**
   - Current: `top_k=5`, `similarity_threshold=0.3` hardcoded in many places
   - Missing: Adaptive parameters based on context
   - Impact: Not optimized for different query types

4. **No Result Deduplication**
   - Current: No mechanism to avoid duplicate context
   - Missing: Semantic deduplication
   - Impact: May include similar memories wasting tokens

5. **No Token Budget Management**
   - Current: Count-based limiting (top_k)
   - Missing: Token-based limiting
   - Impact: May exceed context window with long memories

### 4.3 Recommended Improvements

| Priority | Improvement | Complexity | Impact |
|----------|-------------|-----------|--------|
| High | Add recency weighting to ranking | Medium | High |
| High | Implement token budget management | Medium | High |
| Medium | Add query expansion | Medium | Medium |
| Medium | Add result deduplication | Low | Medium |
| Low | Adaptive thresholds per memory type | Low | Low |

---

## 5. Advanced Techniques

### 5.1 Memory-Based Prompt Engineering

**Chain-of-Memory Pattern:**
```python
async def enhanced_inject_memory_context(query: str, conversation_history: list) -> str:
    # Step 1: Get immediate context from recent conversation
    recent_memories = await get_recent_memories(conversation_history[-3:], top_k=2)
    
    # Step 2: Get long-term relevant memories
    long_term_memories = await search_memories(query, top_k=3)
    
    # Step 3: Combine with priority
    combined = prioritize_memories(
        recent_memories + long_term_memories,
        weights={"recency": 0.5, "relevance": 0.3, "importance": 0.2}
    )
    
    # Step 4: Format with attribution
    return format_memory_context(combined, sources=["recent", "long-term"])
```

**Self-Correction Pattern:**
```python
async def verify_and_inject(memories: list[Memory], query: str) -> list[Memory]:
    verified = []
    for memory in memories:
        # Verify relevance with second pass
        verification_score = await verify_relevance(query, memory.content)
        if verification_score > 0.5:
            verified.append(memory)
    return verified
```

### 5.2 Multi-Step Retrieval

```python
async def multi_step_retrieve(query: str, memory_types: list[MemoryType]) -> list[Memory]:
    # Step 1: Broad retrieval
    broad_results = await search_memories(query, top_k=10, threshold=0.2)
    
    # Step 2: Category-specific refinement
    refined = {}
    for mem_type in memory_types:
        type_results = [m for m in broad_results if m.memory_type == mem_type]
        # Keep top 2 per type
        refined[mem_type] = type_results[:2]
    
    # Step 3: Cross-type consolidation
    all_refined = []
    for results in refined.values():
        all_extended.extend(results)
    
    # Step 4: Final ranking
    return rank_by_composite_score(all_refined, query)
```

### 5.3 Caching Strategies

**Query Result Cache:**
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_memories(query_hash: str, top_k: int) -> tuple:
    """Cache memory search results."""
    # In production, use Redis for distributed caching
    pass

def cache_key(query: str, memory_types: tuple, agent_id: str | None) -> str:
    raw = f"{query}:{memory_types}:{agent_id}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

**Session-Level Cache:**
```python
class SessionMemoryCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def get(self, query: str) -> list[Memory] | None:
        if query in self._cache:
            result, timestamp = self._cache[query]
            if time.time() - timestamp < self._ttl:
                return result
        return None
    
    def set(self, query: str, results: list[Memory]) -> None:
        self._cache[query] = (results, time.time())
```

---

## 6. Implementation Recommendations

### 6.1 Quick Wins (1-2 days)

1. **Add recency weighting:**
```python
def calculate_recency_score(created_at: datetime) -> float:
    hours_old = (datetime.utcnow() - created_at).total_seconds() / 3600
    return 1.0 / (1.0 + hours_old / 24)  # Half-life of 24 hours
```

2. **Implement token counting:**
```python
def estimate_tokens(text: str) -> int:
    return len(text) // 4  # Rough approximation
```

3. **Add deduplication:**
```python
def deduplicate_by_similarity(memories: list[Memory], threshold: float = 0.9) -> list[Memory]:
    # Use embeddings to find near-duplicates
    pass
```

### 6.2 Medium Effort (1 week)

1. **Query expansion pipeline**
2. **Adaptive threshold selection**
3. **Session-level caching**

### 6.3 Long-term (2+ weeks)

1. **Cross-encoder re-ranking**
2. **Memory consolidation/summarization**
3. **Encrypted memory storage**

---

## 7. References

- [Anthropic Claude Documentation](https://docs.anthropic.com)
- [LangChain Memory Modules](https://python.langchain.com/docs/modules/memory/)
- [Qdrant Hybrid Search](https://qdrant.tech/articles/hybrid-search/)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir07-rrf.pdf)

---

## 8. Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-03-08 | Claude Code | Initial research document |
