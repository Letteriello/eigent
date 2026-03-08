# Agent Memory Summarization Research

**Date:** 2026-03-08
**Status:** Research Complete
**Purpose:** Technical research for implementing memory summarization in Eigent

---

## 1. Why Summarization Matters

### 1.1 Context Window Limits

Modern LLMs have finite context windows:
- **GPT-4o:** 128K tokens
- **Claude 3.5:** 200K tokens
- **Gemini 2.0:** 1M tokens (but with latency/cost implications)

As agents accumulate memories over time, they exceed these limits. Without summarization:
- Retrieval becomes inefficient (more noise than signal)
- Context injection exceeds available window
- Agent performance degrades significantly

### 1.2 Storage Efficiency

Raw conversation data is inefficient:
- **Verbose:** Natural language contains redundancy
- **Redundant:** Similar patterns repeat across sessions
- **Expensive:** Vector storage costs scale with data volume

Summarization reduces storage requirements by **60-80%** while preserving essential information.

### 1.3 Information Density

A well-structured summary concentrates actionable information:
- Key decisions and outcomes
- Entity facts and relationships
- User preferences and patterns
- Task completion status

---

## 2. Summarization Approaches

### 2.1 LLM-Based Summarization

**How it works:** Use an LLM to generate abstractive summaries of memory content.

**Implementation options:**

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **Full Summarization** | Summarize entire memory block | Complete overview | Expensive, may lose details |
| **Incremental** | Summarize new content, merge with existing | Efficient, maintains context | Complex merge logic |
| **Extractive + Abstractive** | Extract key points, then synthesize | Balanced | Two-step process |

**Prompts for memory summarization:**

```
You are an expert at condensing agent memories while preserving critical information.

Task: Summarize the following agent memories into a concise, structured format.

Requirements:
1. Preserve all factual information (entities, dates, actions)
2. Keep user preferences and stated goals
3. Note any important outcomes or decisions
4. Maintain temporal context (when relevant)
5. Identify patterns across multiple interactions

Format:
- Key Facts (bullet points)
- User Preferences (bullet points)
- Important Decisions/Outcomes (bullet points)
- Patterns/Observations (bullet points)

Memories to summarize:
{memory_content}

Summary:
```

### 2.2 Extraction-Based Summarization

**How it works:** Identify and extract key information without generating new text.

**Techniques:**
- **Key Phrase Extraction:** Noun phrases, named entities
- **Sentence Scoring:** TF-IDF, LLM-based importance
- **Template Filling:** Structured slots for facts

**Implementation in Eigent:**
```python
class ExtractionSummarizer:
    def __init__(self, llm):
        self.llm = llm

    async def extract_summary(self, memories: list[Memory]) -> Memory:
        # Score each memory by importance
        scored = await self._score_memories(memories)

        # Extract top-K most important
        top_memories = sorted(scored, key=lambda x: x.importance)[:50]

        # Convert to structured facts
        facts = self._extract_facts(top_memories)

        return Memory(
            type="summary",
            content=facts,
            importance=1.0,
            memory_type=MemoryType.SEMANTIC
        )
```

### 2.3 Hybrid Approaches

**Recommended for Eigent: Hierarchical Summarization**

```
Level 1: Raw conversations (kept for 7 days)
    ↓ Summarization
Level 2: Session summaries (kept for 30 days)
    ↓ Consolidation
Level 3: Consolidated memory (kept long-term)
    ↓ Extraction
Level 4: Key facts & preferences (permanent)
```

**Benefits:**
- Preserves granularity where needed
- Progressive condensation
- Rollback capability (original data retained until confirmed)

---

## 3. When to Summarize

### 3.1 Age-Based Triggers

| Age Threshold | Action | Rationale |
|--------------|--------|-----------|
| 24 hours | Flag for review | Context becoming stale |
| 7 days | Generate session summary | Full conversation context no longer needed |
| 30 days | Consolidate summaries | Merge related sessions |
| 90 days | Archive or delete | Beyond useful retention |

**Implementation:**
```python
# memory_service.py
async def get_memories_for_summarization() -> list[Memory]:
    """Get memories ready for summarization based on age."""
    cutoff = datetime.utcnow() - timedelta(days=7)
    return await memory_repo.find_old_unsummarized(cutoff)
```

### 3.2 Size Thresholds

**Token-based triggers:**
- Memory block exceeds 4000 tokens → partial summarization
- Total session memories exceed 8000 tokens → full session summary
- Agent context injection exceeds 50% of window → prioritize retrieval

**Implementation:**
```python
def should_summarize(memories: list[Memory]) -> bool:
    total_tokens = sum(self._estimate_tokens(m.content) for m in memories)
    return total_tokens > SUMMARIZATION_THRESHOLD
```

### 3.3 Importance Scoring

**Factors for prioritization:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Recency | 0.3 | How recently accessed/modified |
| Access Frequency | 0.2 | How often retrieved |
| Content Type | 0.2 | Preferences > Facts > Context |
| Explicit Importance | 0.3 | User/agent marked importance |

**Formula:**
```
summarization_priority = (recency_score * 0.3) +
                         (access_freq * 0.2) +
                         (content_weight * 0.2) +
                         (explicit_importance * 0.3)
```

---

## 4. Preserving Key Information

### 4.1 Entity Retention

**Must preserve:**
- Names (people, organizations, projects)
- Locations and dates
- Technical entities (APIs, tools, configurations)
- Relationships between entities

**Extraction strategy:**
```python
ENTITY_TYPES = {
    "person": ["user", "agent", "developer"],
    "organization": ["company", "team", "project"],
    "technical": ["api", "tool", "function", "endpoint"],
    "temporal": ["date", "time", "deadline", "schedule"]
}

async def extract_entities(memories: list[Memory]) -> dict[str, list[str]]:
    # Use NER or LLM extraction
    entities = await self.llm.extract_entities(memories)
    return organize_by_type(entities)
```

### 4.2 Preference Preservation

**Categories to track:**
- Explicit preferences (user stated directly)
- Implicit preferences (inferred from behavior)
- Workstyle preferences (communication, timing)
- Technical preferences (tools, formats)

**Storage format:**
```python
class UserPreference(BaseModel):
    category: str  # "communication", "technical", "workstyle"
    key: str       # e.g., "response_length", "preferred_language"
    value: Any
    confidence: float  # How certain we are
    source: str       # Which memory this came from
    created_at: datetime
    updated_at: datetime
```

### 4.3 Context Continuity

**Preserving narrative flow:**
1. **Timeline reconstruction:** Maintain chronological ordering
2. **Causal links:** What led to what
3. **Outcome tracking:** What succeeded/failed
4. **Thread continuity:** Related topics across sessions

**Implementation:**
```python
class ContextContinuity:
    def preserve_continuity(self, old_summary: Memory, new_content: list[Memory]) -> str:
        """Merge new content with existing summary maintaining flow."""
        prompt = f"""
        Existing summary:
        {old_summary.content}

        New memories to integrate:
        {self._format_memories(new_content)}

        Create an updated summary that:
        1. Incorporates new information naturally
        2. Maintains temporal and causal relationships
        3. Preserves key entities and facts

        Updated summary:
        """
        return self.llm.generate(prompt)
```

---

## 5. Integration with Eigent

### 5.1 Current Architecture Review

**Existing components:**
- `backend/app/model/memory.py` - Pydantic models
- `backend/app/service/memory_service.py` - CRUD + search
- `backend/app/agent/toolkit/memory_toolkit.py` - Agent tools
- `src/store/memoryStore.ts` - Zustand store

**Current memory types:**
- `fact` - Factual information
- `context` - Conversational context
- `learned` - Semantic knowledge
- `preference` - User preferences

### 5.2 Implementation Plan

**Phase 1: Summarization Service**
```python
# backend/app/service/summarization_service.py

class SummarizationService:
    def __init__(self, llm, memory_service):
        self.llm = llm
        self.memory_service = memory_service

    async def summarize_session(self, session_id: str) -> Memory:
        """Generate summary for a single session."""
        memories = await self.memory_service.get_session_memories(session_id)

        prompt = self._build_summary_prompt(memories)
        summary = await self.llm.generate(prompt)

        summary_memory = Memory(
            type="session_summary",
            content=summary,
            importance=0.8,
            memory_type=MemoryType.SEMANTIC,
            metadata={"session_id": session_id, "source_memories": len(memories)}
        )

        return await self.memory_service.create(summary_memory)

    async def consolidate_summaries(self, time_window: days = 30) -> Memory:
        """Merge multiple summaries into consolidated memory."""
        summaries = await self.memory_service.get_recent_summaries(time_window)
        # ... consolidation logic
```

**Phase 2: Trigger System**
```python
# backend/app/service/summarization_scheduler.py

class SummarizationScheduler:
    def __init__(self, summarization_service, memory_repo):
        self.service = summarization_service
        self.repo = memory_repo

    async def run_scheduled_summarization(self):
        """Run periodic summarization tasks."""
        # 1. Summarize sessions older than 7 days
        old_sessions = await self.repo.get_sessions_older_than(7)
        for session in old_sessions:
            await self.service.summarize_session(session.id)

        # 2. Consolidate summaries older than 30 days
        await self.service.consolidate_summaries(30)
```

**Phase 3: API Endpoints**
```python
# backend/app/controller/memory_controller.py additions

@router.post("/memories/{id}/summarize")
async def summarize_memory(id: str, background_tasks: BackgroundTasks):
    """Manually trigger summarization for a memory."""
    # Implementation

@router.get("/memories/summaries/pending")
async def get_pending_summaries():
    """Get memories pending summarization."""
    # Implementation

@router.get("/memories/{id}/summary")
async def get_memory_summary(id: str):
    """Get the generated summary for a memory."""
    # Implementation
```

### 5.3 Frontend Considerations

**UI Components needed:**

| Component | Purpose | Priority |
|-----------|---------|----------|
| MemoryTimeline | Show memory history with summarization markers | High |
| SummaryViewer | Display generated summaries with source expansion | High |
| SummarizationSettings | Configure triggers and retention | Medium |
| MemoryQualityIndicator | Show summary quality vs raw data | Low |

**Store updates:**
```typescript
// src/store/memoryStore.ts additions
interface MemorySummary {
  id: string;
  memoryId: string;
  content: string;
  sourceCount: number;
  generatedAt: Date;
  quality: 'excellent' | 'good' | 'partial';
}

interface MemoryStore {
  // ... existing state
  summaries: Record<string, MemorySummary>;
  summarizationStatus: 'idle' | 'summarizing' | 'error';

  // ... existing actions
  summarizeMemory: (id: string) => Promise<void>;
  getSummary: (memoryId: string) => MemorySummary | null;
}
```

### 5.4 Configuration Options

```python
# backend/app/model/settings.py

class SummarizationSettings(BaseModel):
    # Triggers
    age_threshold_days: int = 7
    token_threshold: int = 4000

    # What to summarize
    include_context: bool = True
    include_facts: bool = True
    include_preferences: bool = True

    # Generation
    llm_model: str = "gpt-4o-mini"
    summary_length_tokens: int = 500

    # Retention
    keep_raw_after_summary: bool = True
    raw_retention_days: int = 30

    # Schedule
    auto_summarize: bool = True
    schedule_cron: str = "0 2 * * *"  # 2 AM daily
```

---

## 6. Summary

| Aspect | Recommendation |
|--------|----------------|
| **Approach** | Hierarchical: session summaries → consolidated → key facts |
| **Trigger** | Age-based (7 days) + size-based (4000 tokens) |
| **Preservation** | Entity extraction + preference tracking + context continuity |
| **Integration** | New summarization service + scheduler + API endpoints |
| **Frontend** | Summary viewer + timeline integration |

---

## 7. References

- [LangChain ConversationSummaryMemory](https://python.langchain.com/docs/modules/memory/types/summary)
- [Anthropic Memory Guidance](https://docs.anthropic.com/en/docs/memory-guidance)
- [MemGPT Architecture](https://github.com/MemGPT/MemGPT)
- [CrewAI Memory Implementation](https://docs.crewai.com/memory/)

---

*Document version: 1.0*
*Next: Implementation planning based on this research*
