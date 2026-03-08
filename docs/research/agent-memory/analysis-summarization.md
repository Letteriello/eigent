# Memory Summarization Analysis

**Date:** 2026-03-08
**Status:** Implementation Analysis Complete
**Author:** Backend Developer Agent

---

## 1. Architecture Design

### 1.1 Current State

The memory system currently provides:

- **CRUD operations** via `MemoryService` (create, read, update, delete)
- **Hybrid search** combining Qdrant vector search + BM25 with Reciprocal Rank Fusion
- **Session-based storage** with agent_id and session_id fields
- **Memory types:** fact, preference, context, learned (from MemoryType enum)

### 1.2 Proposed Summarization Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Service Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │  MemoryService  │───▶│  SummarizationService        │   │
│  │  (existing)      │    │  - summarize_session()     │   │
│  │                  │    │  - consolidate_summaries()  │   │
│  │                  │    │  - extract_key_facts()     │   │
│  └─────────────────┘    └──────────────────────────────┘   │
│           │                         │                        │
│           ▼                         ▼                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           SummarizationScheduler                     │   │
│  │  - Age-based triggers (7/30/90 days)                │   │
│  │  - Size-based triggers (token thresholds)           │   │
│  │  - Background task execution                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Hierarchical Summarization Levels

| Level | Name                    | Trigger      | Retention | Storage                            |
| ----- | ----------------------- | ------------ | --------- | ---------------------------------- |
| 1     | Raw Conversations       | N/A (source) | 7 days    | Original memories                  |
| 2     | Session Summary         | 7 days old   | 30 days   | New memory (type: session_summary) |
| 3     | Consolidated Memory     | 30 days old  | Long-term | New memory (type: consolidated)    |
| 4     | Key Facts & Preferences | 90 days old  | Permanent | Entity extraction results          |

---

## 2. Files to Create/Modify

### 2.1 New Files to Create

| File                                             | Purpose                                    | Priority |
| ------------------------------------------------ | ------------------------------------------ | -------- |
| `backend/app/service/summarization_service.py`   | Core summarization logic (LLM-based)       | P0       |
| `backend/app/service/summarization_scheduler.py` | Trigger system for automatic summarization | P1       |
| `backend/app/model/summarization.py`             | Pydantic models for summarization API      | P1       |
| `backend/app/service/entity_extraction.py`       | Entity and preference extraction           | P2       |
| `frontend/src/types/summarization.ts`            | TypeScript types for frontend              | P1       |

### 2.2 Files to Modify

| File                                          | Changes                                                        | Priority |
| --------------------------------------------- | -------------------------------------------------------------- | -------- |
| `backend/app/model/memory.py`                 | Add new memory types: session_summary, consolidated, key_facts | P0       |
| `backend/app/model/enums.py`                  | Add MemoryType enum values                                     | P0       |
| `backend/app/service/memory_service.py`       | Add session-based query methods                                | P1       |
| `backend/app/controller/memory_controller.py` | Add summarization API endpoints                                | P1       |
| `src/store/memoryStore.ts`                    | Add summarization state and actions                            | P1       |
| `src/pages/Agents/Memory.tsx`                 | Add summary viewer UI                                          | P2       |

---

## 3. API Endpoints Needed

### 3.1 New Endpoints

| Method | Endpoint                                       | Purpose                                             |
| ------ | ---------------------------------------------- | --------------------------------------------------- |
| POST   | `/api/memories/{id}/summarize`                 | Manually trigger summarization for a memory/session |
| GET    | `/api/memories/summaries/pending`              | Get memories pending summarization                  |
| GET    | `/api/memories/{id}/summary`                   | Get generated summary for a memory                  |
| POST   | `/api/memories/summarize/session/{session_id}` | Summarize all memories in a session                 |
| GET    | `/api/memories/settings`                       | Get summarization configuration                     |
| PUT    | `/api/memories/settings`                       | Update summarization settings                       |
| POST   | `/api/memories/scheduler/run`                  | Manually trigger scheduled summarization            |

### 3.2 Request/Response Models

```python
# Request: POST /api/memories/{id}/summarize
class SummarizeRequest(BaseModel):
    summary_type: Literal["session", "consolidated", "key_facts"]
    force: bool = False  # Override age threshold

# Response: GET /api/memories/{id}/summary
class SummaryResponse(BaseModel):
    memory_id: str
    summary_id: str
    content: str
    summary_type: str
    source_memory_count: int
    generated_at: datetime
    quality: Literal["excellent", "good", "partial"]

# Settings: PUT /api/memories/settings
class SummarizationSettings(BaseModel):
    age_threshold_days: int = 7
    token_threshold: int = 4000
    llm_model: str = "gpt-4o-mini"
    summary_length_tokens: int = 500
    auto_summarize: bool = True
    keep_raw_after_summary: bool = True
    raw_retention_days: int = 30
```

---

## 4. Frontend Changes

### 4.1 Store Updates (`src/store/memoryStore.ts`)

```typescript
interface MemorySummary {
  id: string;
  memoryId: string;
  content: string;
  summaryType: 'session_summary' | 'consolidated' | 'key_facts';
  sourceMemoryCount: number;
  generatedAt: string;
  quality: 'excellent' | 'good' | 'partial';
}

interface SummarizationSettings {
  ageThresholdDays: number;
  tokenThreshold: number;
  llmModel: string;
  summaryLengthTokens: number;
  autoSummarize: boolean;
  keepRawAfterSummary: boolean;
  rawRetentionDays: number;
}

interface MemoryStore {
  // ... existing state
  summaries: Record<string, MemorySummary>;
  summarizationStatus: 'idle' | 'summarizing' | 'error';
  summarizationSettings: SummarizationSettings;
  pendingSummaries: string[]; // memory IDs pending summarization

  // New actions
  summarizeMemory: (id: string, type: string) => Promise<void>;
  getSummary: (memoryId: string) => Promise<MemorySummary | null>;
  fetchPendingSummaries: () => Promise<void>;
  updateSummarizationSettings: (
    settings: Partial<SummarizationSettings>
  ) => Promise<void>;
  runScheduledSummarization: () => Promise<void>;
}
```

### 4.2 UI Components

| Component                    | Purpose                                         | Priority |
| ---------------------------- | ----------------------------------------------- | -------- |
| `MemorySummaryCard`          | Display generated summary with source expansion | P1       |
| `SummarizationSettingsPanel` | Configure triggers and retention                | P2       |
| `MemoryTimeline`             | Show memory history with summarization markers  | P2       |

---

## 5. Implementation Priority

### Phase 1: Core Summarization (Week 1)

1. Add new memory types to enum
2. Create `SummarizationService` with LLM-based summarization
3. Add session-based query methods to `MemoryService`
4. Implement basic summarization endpoint

### Phase 2: Scheduler & API (Week 2)

1. Create `SummarizationScheduler` with age/size triggers
2. Add all API endpoints
3. Implement settings persistence
4. Add background task support (FastAPI BackgroundTasks)

### Phase 3: Frontend Integration (Week 3)

1. Update memoryStore with summarization state
2. Create summary viewer components
3. Add settings UI panel

### Phase 4: Advanced Features (Week 4)

1. Entity extraction service
2. Preference tracking
3. Quality scoring
4. Memory timeline visualization

---

## 6. Key Implementation Details

### 6.1 Summarization Service

```python
class SummarizationService:
    async def summarize_session(self, session_id: str) -> MemoryResponse:
        """Generate summary for all memories in a session."""
        memories = await self.memory_service.get_session_memories(session_id)
        prompt = self._build_summary_prompt(memories)
        summary_content = await self.llm.generate(prompt)

        summary_memory = MemoryCreate(
            content=summary_content,
            memory_type=MemoryType.SESSION_SUMMARY,
            metadata={
                "session_id": session_id,
                "source_memory_count": len(memories),
                "source_memory_ids": [m.id for m in memories]
            }
        )
        return await self.memory_service.create_memory(summary_memory)
```

### 6.2 Scheduler Logic

```python
class SummarizationScheduler:
    async def run_scheduled_summarization(self):
        # 1. Find sessions older than 7 days without summaries
        old_sessions = await self.repo.get_sessions_without_summary(7)
        for session in old_sessions:
            await self.service.summarize_session(session.id)

        # 2. Consolidate summaries older than 30 days
        old_summaries = await self.repo.get_summaries_older_than(30)
        if old_summaries:
            await self.service.consolidate_summaries(old_summaries)
```

### 6.3 Entity Extraction

```python
class EntityExtractionService:
    ENTITY_TYPES = ["person", "organization", "technical", "temporal"]

    async def extract_key_facts(self, memories: list[Memory]) -> dict:
        """Extract structured facts for permanent storage."""
        prompt = f"""
        Extract key entities and facts from these memories.
        Categories: {', '.join(self.ENTITY_TYPES)}

        Memories:
        {format_memories(memories)}

        Return as structured JSON:
        """
        return await self.llm.extract_json(prompt)
```

---

## 7. Configuration Options

| Setting                  | Default     | Description                         |
| ------------------------ | ----------- | ----------------------------------- |
| `age_threshold_days`     | 7           | Days before session is summarized   |
| `token_threshold`        | 4000        | Tokens before forcing summarization |
| `llm_model`              | gpt-4o-mini | Model for summarization             |
| `summary_length_tokens`  | 500         | Target summary length               |
| `auto_summarize`         | True        | Enable automatic summarization      |
| `keep_raw_after_summary` | True        | Keep raw data after summarization   |
| `raw_retention_days`     | 30          | Days to keep raw data               |

---

## 8. Risks & Mitigations

| Risk                | Impact   | Mitigation                                     |
| ------------------- | -------- | ---------------------------------------------- |
| LLM cost            | High     | Use cheap model (gpt-4o-mini), cache summaries |
| Data loss           | Critical | Keep raw data until summary confirmed          |
| Quality degradation | Medium   | Quality scoring, manual review option          |
| Context overflow    | High     | Token-based triggers, priority scoring         |

---

## 9. Summary

| Aspect           | Recommendation                                               |
| ---------------- | ------------------------------------------------------------ |
| **Approach**     | Hierarchical: session summaries → consolidated → key facts   |
| **Trigger**      | Age-based (7/30/90 days) + size-based (4000 tokens)          |
| **Preservation** | Entity extraction + preference tracking + context continuity |
| **Integration**  | New summarization service + scheduler + API endpoints        |
| **Frontend**     | Summary viewer + settings panel + timeline integration       |

---

_Document version: 1.0_
_Ready for implementation planning_
