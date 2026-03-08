# Agent Memory Implementation Plan

**Date:** 2026-03-08
**Status:** Draft
**Based on:** 9 research documents

---

## Executive Summary

This plan prioritizes improvements for the Eigent memory module based on comprehensive research across 9 areas.

---

## Current State Analysis

### What's Working ✅
- MemoryService with hybrid search (BM25 + Vector + RRF)
- 4 memory types: fact, preference, context, learned
- MemoryToolkit with 5 tools for agents
- Context injection for prompts
- Frontend UI with Zustand store

### Gaps Identified ❌
- No encryption at rest
- No summarization
- No entity extraction
- No working memory (context window only)
- No consolidation/cleanup
- Basic multi-agent support

---

## Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Memory Summarization | High | Medium | 🔴 P1 |
| Encryption/Security | High | Medium | 🔴 P1 |
| Context Injection Improvements | High | Low | 🔴 P1 |
| Working Memory | Medium | Medium | 🟡 P2 |
| Entity Extraction | Medium | High | 🟡 P2 |
| Memory Consolidation | Medium | Low | 🟢 P3 |
| Multi-Agent Memory | Low | High | 🟢 P3 |

---

## Implementation Phases

### Phase 1: Quick Wins (1-2 weeks)

#### 1.1 Context Injection Improvements
**Files:** `backend/app/utils/memory_context.py`

**Changes:**
- Add priority scoring (importance + recency + relevance)
- Add truncation with composite score
- Add token budget management

**Code:**
```python
priority_score = (importance * 0.4) + (recency * 0.3) + (relevance * 0.3)
```

#### 1.2 Memory Consolidation
**Files:** `backend/app/service/memory_service.py`

**Changes:**
- Add deduplication logic
- Add cleanup scheduler
- Add API endpoint for manual cleanup

#### 1.3 Configuration Settings
**Files:** New `backend/app/model/memory_settings.py`

**Add:**
- Token thresholds
- Age-based triggers
- Retention policies

---

### Phase 2: Core Features (2-4 weeks)

#### 2.1 Memory Summarization
**Files:** New `backend/app/service/summarization_service.py`

**Architecture:**
```
Level 1: Raw memories (7 days)
Level 2: Session summaries (30 days)
Level 3: Consolidated (90 days)
Level 4: Key facts (permanent)
```

**Implementation:**
- SummarizationService class
- Scheduler (daily/weekly)
- API endpoints for manual trigger
- Frontend: Summary viewer

#### 2.2 Encryption
**Files:** `backend/app/service/memory_service.py`

**Changes:**
- Add field-level encryption for sensitive content
- Add encryption key management
- Add PII detection (optional)

**Options:**
- `cryptography` library for field encryption
- Qdrant built-in encryption (if available)

---

### Phase 3: Advanced Features (4-8 weeks)

#### 3.1 Working Memory
**Files:** New `backend/app/service/working_memory.py`

**Features:**
- In-context memory (not persisted)
- Sliding window
- Priority-based retention

#### 3.2 Entity Extraction
**Files:** New `backend/app/service/entity_service.py`

**Features:**
- NER extraction
- Knowledge graph storage
- Relationship tracking

**Options:**
- Use LLM for extraction (recommended)
- spaCy for lightweight extraction

#### 3.3 Multi-Agent Memory
**Files:** `backend/app/service/memory_service.py`

**Changes:**
- Add team_id/project_id fields
- Add shared memory flag
- Add team query API

---

## Files to Create/Modify

### New Files
```
backend/app/model/memory_settings.py      # Configuration
backend/app/service/summarization_service.py  # Phase 2
backend/app/service/encryption_service.py  # Phase 2
backend/app/service/entity_service.py      # Phase 3
backend/app/service/working_memory.py      # Phase 3
```

### Files to Modify
```
backend/app/service/memory_service.py      # Add consolidation
backend/app/utils/memory_context.py        # Improve injection
backend/app/agent/toolkit/memory_toolkit.py # Add new tools
backend/app/controller/memory_controller.py # Add endpoints
src/store/memoryStore.ts                  # Add new state
src/pages/Agents/Memory.tsx                # Add UI
```

---

## API Endpoints to Add

| Method | Endpoint | Phase |
|--------|----------|-------|
| POST | `/api/memory/{id}/summarize` | P2 |
| GET | `/api/memory/summaries/pending` | P2 |
| POST | `/api/memory/consolidate` | P1 |
| DELETE | `/api/memory/cleanup` | P1 |
| GET | `/api/memory/entities` | P3 |
| POST | `/api/memory/team/shared` | P3 |

---

## Frontend Changes

### Phase 1
- Memory timeline with age indicators
- Cleanup settings UI
- Summary preview

### Phase 2
- Full summarization controls
- Manual trigger buttons
- Summary viewer

### Phase 3
- Entity viewer
- Knowledge graph visualization
- Team memory UI

---

## Testing Strategy

1. **Unit Tests:** Service layer
2. **Integration Tests:** API endpoints
3. **E2E Tests:** Full user flows
4. **Performance Tests:** Search latency

---

## Rollout Plan

1. **Deploy Phase 1** - Context improvements + consolidation
2. **Monitor** - Search quality metrics
3. **Deploy Phase 2** - Summarization + encryption
4. **Monitor** - Storage usage, retrieval quality
5. **Deploy Phase 3** - Advanced features

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Retrieval accuracy | > 85% |
| Search latency | < 100ms |
| Memory storage | < 1GB per 10k memories |
| Summarization quality | > 80% info retention |

---

## Next Steps

1. **Approve this plan** ✅
2. **Start Phase 1** - Context injection improvements
3. **Weekly review** - Track progress
4. **Iterate** - Based on user feedback

---

*Document version: 1.0*
*Created from: 9 research documents in docs/research/agent-memory/*
