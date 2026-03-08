# Agent Memory Types - Comprehensive Research

**Date:** 2026-03-08
**Status:** Research Complete
**File:** docs/research/agent-memory/memory-types.md

---

## Executive Summary

This document provides a comprehensive analysis of different memory types for AI agents, their implementation approaches in popular frameworks (LangChain, AutoGen, CrewAI), and integration recommendations for the Eigent platform.

**Current Eigent Status:**
- Episodic/Semantic: ✅ Implemented via `fact`, `learned`, `context` types
- Preference: ✅ Implemented via `preference` type
- Working Memory: ⚠️ Not implemented (context window only)
- Procedural Memory: ❌ Not implemented

---

## 1. Episodic Memory

### Definition
Episodic memory stores records of specific events or experiences—the "what happened" memory. In AI agents, this captures individual interactions, conversations, and task executions.

### Implementation Approaches

#### 1.1 Storage Strategies
| Approach | Description | Best For |
|----------|-------------|----------|
| Conversation Logs | Store full conversation history | Debugging, audit trails |
| Event Sourcing | Store state changes as events | Complex workflows |
| Summarized Episodes | Compress events into summaries | Long-running agents |
| Vector Stores | Embed episodes for semantic retrieval | Context-aware recall |

#### 1.2 Framework Implementations

**LangChain:**
```python
# ConversationBufferMemory - stores raw messages
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory(return_messages=True)

# ConversationSummaryMemory - stores summaries
from langchain.memory import ConversationSummaryMemory
memory = ConversationSummaryMemory(llm=llm)

# ConversationEntityMemory - extracts entities
from langchain.memory import ConversationEntityMemory
memory = ConversationEntityMemory(llm=llm)
```

**AutoGen:**
- `PersistentMemory` plugin for cross-session persistence
- User proxy memory for tracking user interactions
- Event logging for audit trails

**CrewAI:**
- Agent-specific memory storage
- SQLite-based episodic storage
- Integration with vector stores for retrieval

### When to Use Episodic Memory
- ✅ User conversation history
- ✅ Task execution history
- ✅ Error recovery and debugging
- ✅ Personalization based on past interactions

### Eigent Integration
**Current Implementation:** Eigent already implements episodic-like memory via:
- `MemoryType.fact` - factual events
- `MemoryType.context` - working context events
- `session_id` for episode grouping

**Recommendation:** Add explicit episode metadata (timestamp, participants, outcome) for better retrieval.

---

## 2. Semantic Memory

### Definition
Semantic memory stores general knowledge, facts, and concepts—independent of personal experience. It's the "knowing that" memory rather than "knowing of."

### How It Differs from Episodic

| Aspect | Episodic | Semantic |
|--------|----------|----------|
| Nature | Personal experiences | General facts |
| Structure | Event-based | Concept-based |
| Retrieval | Context-dependent | Query-dependent |
| Updates | Append-only | Mutable |

### Storage Strategies

#### 2.1 Knowledge Bases
- Structured KB (JSON, RDF)
- Unstructured documents
- Graph databases (Neo4j)

#### 2.2 Vector Store Approaches
```python
# Semantic memory as vector store
from camel.storages import QdrantStorage

storage = QdrantStorage(
    vector_dim=1536,
    collection_name="semantic_memory"
)
```

#### 2.3 Framework Implementations

**LangChain:**
```python
# Knowledge graph memory
from langchain.memory import ConversationKnowledgeGraphMemory

# Entity memory with structured storage
memory = ConversationEntityMemory(llm=llm, entity_store="sql")

# Vector store retriever
from langchain.memory import VectorStoreRetrieverMemory
memory = VectorStoreRetrieverMemory(retriever=retriever)
```

**AutoGen:**
- Knowledge base integration
- RAG (Retrieval-Augmented Generation) pipelines

**CrewAI:**
- Shared knowledge base
- Tool usage knowledge
- Process memory

### Retrieval Patterns

1. **Semantic Search:** Vector similarity
2. **Keyword Search:** BM25 for exact matches
3. **Hybrid:** RRF fusion (what Eigent uses)
4. **Graph Traversal:** For related concepts

### Eigent Integration
**Current Implementation:** 
- `MemoryType.learned` - stores general knowledge
- Hybrid search (vector + BM25 + RRF) ✅

**Recommendation:** Add knowledge graph layer for concept relationships.

---

## 3. Working Memory

### Definition
Working memory is short-term, temporary storage for information currently being processed. It's the "scratchpad" for the current task—information readily accessible but not persisted.

### In-Context vs Persistent Working Memory

| Type | Storage | Lifespan | Capacity |
|------|---------|----------|----------|
| In-Context | LLM context window | Current turn | ~128K tokens |
| Persistent Working | Fast storage | Session | ~MB |
| Session State | Database | Hours/Days | Unlimited |

### Implementation Approaches

#### 3.1 Context Window Management
```python
# LangChain's window buffer
from langchain.memory import ConversationBufferWindowMemory
memory = ConversationBufferWindowMemory(k=5)  # Last 5 exchanges
```

#### 3.2 Structured State
```python
# Task state for working memory
class WorkingMemory:
    current_task: str
    sub_goals: List[str]
    completed_steps: List[str]
    context: Dict[str, Any]
    artifacts: List[Document]
```

#### 3.3 Framework Implementations

**LangChain:**
- `ConversationBufferWindowMemory` - k recent messages
- `ConversationTokenBufferMemory` - token-based limit
- Custom state machines for complex workflows

**AutoGen:**
- Group chat state management
- Speaker selection state
- Task decomposition state

**CrewAI:**
- Agent scratchpad
- Task execution state
- Iteration counters

### Context Window Management

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Context Window                       │
├─────────────────────────────────────────────────────────────┤
│ System Prompt  │  Working Memory  │  Recent History        │
│    (fixed)     │    (priority)    │   (fallback)           │
└─────────────────────────────────────────────────────────────┘
```

**Strategies:**
1. **Priority-based:** Working memory > episodic > semantic
2. **Token budgeting:** Reserve X tokens for each component
3. **Compression:** Summarize older content when near limit
4. **Lazy loading:** Load relevant memories on-demand

### Eigent Integration
**Current Status:** NOT IMPLEMENTED

**Recommendation:** Implement session-scoped working memory:
```python
# Proposed working memory structure
class WorkingMemory:
    session_id: str
    current_task: TaskContext
    relevant_memories: List[Memory]  # Retrieved from storage
    tool_usage_history: List[ToolUse]
    artifacts: Dict[str, Any]
```

---

## 4. Procedural Memory

### Definition
Procedural memory is knowing "how to do" things—skills, patterns, and procedures. In AI agents, this includes tool usage patterns, workflow sequences, and learned behaviors.

### Task Patterns Learned

| Pattern | Description | Example |
|---------|-------------|---------|
| Tool Sequences | Common tool combinations | Search → Summarize → Format |
| Error Recovery | Known error → Fix mappings | Timeout → Retry with backoff |
| Workflow Templates | Reusable task structures | Code Review → Test → Deploy |
| Agent Coordination | Multi-agent patterns | Research → Implement → Review |

### Tool Usage History

```python
# Track tool usage patterns
class ToolUsageRecord:
    tool_name: str
    parameters: Dict
    result: Any
    success: bool
    duration_ms: int
    timestamp: datetime

# Analyze patterns
def find_common_patterns(usage_history: List[ToolUsageRecord]) -> List[Pattern]:
    # Sequential pattern mining
    # Frequency analysis
    # Success rate correlation
```

### Framework Implementations

**LangChain:**
```python
# Tool usage agents
from langchain.agents import AgentExecutor

# Custom agent with procedural memory
class ProceduralAgent:
    def learn_pattern(self, sequence: List[Action]):
        self.patterns.append(sequence)
    
    def apply_pattern(self, task: Task) -> List[Action]:
        # Match task to known patterns
        return self.patterns.get_matching(task)
```

**AutoGen:**
- Tool registration and caching
- Agent skill library
- Workflow automation

**CrewAI:**
- Task templates
- Process workflows
- Tool orchestration

### Eigent Integration
**Current Status:** NOT IMPLEMENTED

**Recommendation:** Add procedural memory toolkit:
```python
class ProceduralMemoryToolkit:
    """Tools for learning and applying procedures"""
    
    async def remember_procedure(
        self,
        name: str,
        steps: List[str],
        context: str
    ) -> str:
        """Store a procedure pattern"""
        
    async def recall_procedure(
        self,
        task_description: str
    ) -> str:
        """Find relevant procedures"""
        
    async def apply_procedure(
        self,
        procedure_name: str,
        parameters: Dict
    ) -> str:
        """Execute a known procedure"""
```

---

## 5. Preference Memory

### Definition
Preference memory stores user preferences, settings, and behavioral patterns. This is critical for personalized AI experiences.

### Current Eigent Implementation Analysis

**Status:** ✅ IMPLEMENTED

**Existing Implementation:**
```python
# Memory toolkit provides remember_preference
async def remember_preference(
    self,
    preference: str,
    context: str | None = None,
    importance: float = 0.9,
) -> str:
```

**Memory Types:**
- `MemoryType.preference` - explicit preferences
- `importance` field (0-1) for prioritization
- `metadata.context` for contextual preferences

### Completeness Assessment

| Feature | Status | Notes |
|---------|--------|-------|
| Explicit preferences | ✅ | `remember_preference` tool |
| Implicit preferences | ❌ | Not extracted from behavior |
| Preference conflict resolution | ❌ | Last-write-wins only |
| Preference validation | ❌ | No schema validation |
| Contextual preferences | ⚠️ | Context field exists, not used |
| Preference expiration | ❌ | No temporal decay |

### Recommendations for Enhancement

1. **Implicit Preference Extraction:**
   ```python
   # Extract preferences from behavior
   class PreferenceExtractor:
       def extract(self, conversation: List[Message]) -> List[Preference]:
           # Analyze language patterns
           # Detect stated preferences
           # Infer from actions
   ```

2. **Preference Schema:**
   ```python
   class PreferenceSchema(BaseModel):
       category: PreferenceCategory  # coding, communication, UI, etc.
       key: str
       value: Any
       confidence: float
       source: PreferenceSource  # explicit, inferred, learned
       expires_at: datetime | None
   ```

3. **Conflict Resolution:**
   ```python
   async def resolve_preference(
       preferences: List[Preference]
   ) -> Preference:
       # Weight by: confidence, recency, source
       # explicit > inferred > learned
   ```

---

## 6. Comparative Analysis

### Memory Type Comparison

| Type | Persistence | Update Frequency | Retrieval | Storage |
|------|-------------|------------------|-----------|---------|
| Episodic | Long-term | Per-event | Semantic search | Vector + text |
| Semantic | Long-term | On-knowledge-change | Hybrid search | Vector + KB |
| Working | Session | Real-time | Direct access | Fast storage |
| Procedural | Long-term | Per-pattern | Sequence matching | Graph + vector |
| Preference | Long-term | On-change | Exact match | Structured DB |

### Framework Feature Matrix

| Feature | LangChain | AutoGen | CrewAI | Eigent |
|---------|-----------|---------|--------|--------|
| Episodic | ✅ | ✅ | ✅ | ✅ |
| Semantic | ✅ | ✅ | ✅ | ✅ |
| Working | ⚠️ | ⚠️ | ⚠️ | ❌ |
| Procedural | ⚠️ | ⚠️ | ✅ | ❌ |
| Preference | ✅ | ✅ | ✅ | ✅ |
| Hybrid Search | ✅ | ✅ | ✅ | ✅ |
| Encryption | ❌ | ❌ | ❌ | ❌ |

---

## 7. Eigent Architecture Recommendations

### Current Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              memoryStore.ts (Zustand)                │   │
│  │   - CRUD operations                                 │   │
│  │   - Local persistence                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ Controller  │  │   Service   │  │    Toolkit       │   │
│  │  (REST API)  │  │  (CRUD+Search)│  │  (Agent Tools)   │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Storage (Qdrant + In-Memory)              │   │
│  │   - Vector search                                    │   │
│  │   - BM25 search                                      │   │
│  │   - RRF fusion                                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Extended Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │ memoryStore  │  │workingMemory │  │preferenceStore │   │
│  │ (persistent) │  │  (session)   │  │  (structured)  │   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Memory Controller (REST)                 │   │
│  │  GET/POST/PUT/DELETE /api/memory/*                   │   │
│  │  GET/POST      /api/working-memory/*                  │   │
│  │  GET/POST/PUT  /api/preferences/*                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │
│  ┌──────────────┐  ┌──────┴──────┐  ┌──────────────────┐  │
│  │   Episodic   │  │   Semantic   │  │    Procedural    │  │
│  │   Service    │  │   Service    │  │     Service      │  │
│  │ (hybrid)     │  │  (hybrid)    │  │   (patterns)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Storage Layer                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────────┐   │   │
│  │  │ Qdrant   │ │ SQLite   │ │ Knowledge Graph   │   │   │
│  │  │(vectors) │ │(struct.) │ │   (relationships)  │   │   │
│  │  └──────────┘ └──────────┘ └───────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Priority

| Priority | Memory Type | Implementation Effort | Impact |
|----------|-------------|----------------------|--------|
| 1 | Working Memory | Medium | High |
| 2 | Preference Enhancement | Medium | Medium |
| 3 | Procedural Memory | High | Medium |
| 4 | Knowledge Graph | High | Low |

---

## 8. Conclusion

Eigent's current memory implementation provides a solid foundation for episodic and semantic memory through its hybrid search architecture. The following improvements are recommended:

1. **Working Memory (High Priority):** Essential for task-focused agents
2. **Preference Memory Enhancement:** Add implicit preference extraction and conflict resolution
3. **Procedural Memory:** For learning and applying task patterns
4. **Security:** Add encryption for sensitive memory data

---

## 9. References

### Documentation
- [LangChain Memory Module](https://python.langchain.com/docs/modules/memory/)
- [AutoGen Memory Topics](https://microsoft.github.io/autogen/docs/topics/)
- [CrewAI Memory System](https://docs.crewai.com/core-concepts/memory/)

### Research Papers
- "Memories, Agents, and Conversations" - Architecture patterns
- "Hybrid Search for RAG" - BM25 + Vector fusion techniques
- "Agent Memory Systems" - Survey of memory architectures

---

*Research completed: 2026-03-08*
