# Multi-Agent Memory Architecture Research

**Date:** 2026-03-08
**Status:** Complete
**Researcher:** Claude Code

---

## Executive Summary

This document explores patterns for implementing multi-agent and shared memory architectures in Eigent. After analyzing the current implementation and researching industry frameworks (CrewAI, AutoGen, LangGraph), we provide recommendations for evolving Eigent's memory system to support collaborative agent workflows.

---

## 1. Multi-Agent Memory Patterns

### 1.1 Memory Scope Types

There are three primary patterns for organizing memory in multi-agent systems:

| Pattern            | Description                            | Use Case                          |
| ------------------ | -------------------------------------- | --------------------------------- |
| **Agent-Specific** | Private memory isolated per agent      | Sensitive data, personal context  |
| **Team/Shared**    | Common memory accessible by all agents | Project context, shared knowledge |
| **Hierarchical**   | Nested scopes (team > agent > session) | Complex organizations             |

### 1.2 CrewAI Pattern (Hierarchical Scoped Memory)

CrewAI implements memory with hierarchical scopes using path-based filtering:

```python
from crewai import Agent, Memory

memory = Memory()

# Agent with private scope - only accesses /agent/researcher
researcher = Agent(
    role="Researcher",
    memory=memory.scope("/agent/researcher"),
)

# Agent using shared crew memory (default when no scope set)
writer = Agent(
    role="Writer",
    # Uses crew._memory when crew has memory enabled
)

# Memories are stored with hierarchical paths:
# /agent/researcher/fact_123 -> only visible to researcher
# /shared/project_x/fact_456 -> visible to all crew agents
```

**Key Features:**

- `memory.scope(path)` creates isolated views
- Scoped memories automatically organized under path
- Shared memories accessible when no agent-specific scope set
- Configurable scoring: `recency_weight`, `semantic_weight`, `importance_weight`

### 1.3 AutoGen Pattern (State Persistence)

AutoGen focuses on team state persistence and restoration:

```python
# Save entire team conversational state
team_state = await agent_team.save_state()

# State includes agent memory + conversation history
with open("state.json", "w") as f:
    json.dump(state, f)

# Restore state for new session
await agent_team.load_state(team_state)
```

**Key Features:**

- `save_state()` captures full team memory + history
- `load_state()` restores context across sessions
- GroupChatManager orchestrates shared communication
- Subscription-based topic routing for inter-agent messages

### 1.4 LangGraph Pattern (Graph-Based)

LangGraph uses checkpointing with typed state:

```python
# State carries memory across nodes
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    memory: dict  # Agent-specific memory
    shared_context: dict  # Team context
```

---

## 2. Access Control Patterns

### 2.1 Read/Write Permissions

| Framework        | Read Access          | Write Access   | Audit           |
| ---------------- | -------------------- | -------------- | --------------- |
| CrewAI           | Path-based filtering | Agent identity | Via metadata    |
| AutoGen          | State isolation      | Agent identity | Via state dump  |
| Eigent (current) | agent_id filter      | agent_id field | Not implemented |

### 2.2 Recommended Access Control Matrix

For Eigent, we recommend implementing:

```
┌─────────────────┬──────────┬──────────┬──────────────┐
│ Memory Type     │ Owner    │ Read     │ Write        │
├─────────────────┼──────────┼──────────┼──────────────┤
│ Agent Private   │ agent_id │ agent_id │ agent_id     │
│ Project Shared  │ project  │ team     │ team + agents│
│ Session         │ session  │ session  │ session      │
│ Global          │ system   │ all      │ admin        │
└─────────────────┴──────────┴──────────┴──────────────┘
```

### 2.3 Audit Logging Requirements

To implement audit logging, track:

- **Actor**: Which agent/user performed the action
- **Action**: CREATE, READ, UPDATE, DELETE
- **Resource**: Memory ID and scope path
- **Timestamp**: UTC timestamp
- **Result**: Success/failure

---

## 3. Implementation Approaches

### 3.1 Option A: Separate Collections Per Agent

```
Qdrant Collections:
├── agent_{agent_id}_private    # Agent-specific memories
├── project_{project_id}_shared  # Project-level memories
└── system_global                # Global knowledge
```

**Pros:**

- Clean isolation
- Easy permission enforcement
- Simple query routing

**Cons:**

- Cross-agent search requires multiple queries
- More collections to manage
- Join operations complex

### 3.2 Option B: Single Collection with Filters (Recommended)

```
Qdrant Collection: agent_memory
├── Payload fields:
│   ├── agent_id: str      # Owner (null = shared)
│   ├── project_id: str    # Project scope
│   ├── session_id: str    # Session scope
│   ├── scope_path: str    # /agent/x/shared/y
│   ├── memory_type: str   # fact, preference, etc.
│   ├── access_level: str  # private, team, public
│   └── created_by: str    # Agent/user who created
```

**Pros:**

- Single query for cross-agent search
- Flexible filtering
- Easier to implement RRF across scopes

**Cons:**

- Requires careful filter validation
- Permission bugs could expose data

### 3.3 Option C: Hybrid Approach

- **Hot data**: In-memory with agent/project indexes
- **Cold data**: Qdrant with scope filters

---

## 4. Real-World Framework Analysis

### 4.1 CrewAI Memory Architecture

**Storage Backend:**

- Default: In-memory with SQLite persistence
- Supports vector stores: Chroma, Pinecone, Qdrant

**Memory Extraction:**

```python
# After each task, crew extracts facts:
crew.memory.remember(
    content="Extracted fact from task output",
    context={"task_id": task.id, "agent": agent.name}
)
```

**Context Injection:**

```python
# Before each task, recall relevant context:
context = await crew.memory.recall(
    query=task.description,
    top_k=5
)
# Injected into task prompt
```

### 4.2 AutoGen Team Memory

**State Components:**

- Agent internal state (memory)
- Conversation history
- Shared context (group chat)

**Persistence:**

```python
# Save/load includes:
{
    "agents": {agent_id: agent_state},
    "messages": [...],
    "shared_context": {...}
}
```

### 4.3 LangGraph Checkpointing

**State Management:**

- Checkpoints at each graph node
- Typed state with memory fields
- Conditional branching based on state

---

## 5. Eigent Current Analysis

### 5.1 Current Implementation

Based on code analysis:

| Component         | Status         | Location                                      |
| ----------------- | -------------- | --------------------------------------------- |
| Memory Model      | ✅ Implemented | `backend/app/model/memory.py`                 |
| Memory Service    | ✅ Implemented | `backend/app/service/memory_service.py`       |
| Memory Toolkit    | ✅ Implemented | `backend/app/agent/toolkit/memory_toolkit.py` |
| Memory Controller | ✅ Implemented | `backend/app/controller/memory_controller.py` |
| Frontend Store    | ✅ Implemented | `src/store/memoryStore.ts`                    |

**Current Features:**

- `agent_id` field for ownership (optional)
- `session_id` for session scoping
- `memory_type`: fact, preference, context, learned
- Hybrid search: BM25 + Vector + RRF
- Qdrant for vector storage

### 5.2 Current Gaps

1. **No Project Isolation**: Memories not tied to project_id
2. **No Access Control**: Anyone can read/write any memory
3. **No Audit Logging**: No action tracking
4. **No Scope Hierarchy**: Flat agent_id structure
5. **No Shared Memory**: No concept of team/project memory
6. **Frontend Limited**: No UI for multi-agent memory management

### 5.3 Current Agent Model

From `backend/app/agent/agent_model.py`:

- Agents are created per task/chat session
- Each agent has unique `agent_id` (UUID)
- Agents tied to `project_id` via task lock
- No explicit memory sharing mechanism between agents

---

## 6. Recommended Approach for Eigent

### 6.1 Phase 1: Add Project Isolation (Quick Win)

**Changes Required:**

1. **Memory Model Updates:**

```python
class MemoryCreate(BaseModel):
    # Add required project_id
    project_id: str = Field(..., description="Project this memory belongs to")

    # Keep existing fields
    agent_id: str | None = Field(default=None, description="Agent owner (null = project shared)")
    access_level: AccessLevel = Field(default=AccessLevel.team, description="private/team/public")
```

2. **Service Updates:**

- Add project_id to all queries by default
- Filter: `project_id = current_project` unless admin

3. **API Updates:**

- Require project_id in create/search requests
- Validate user has access to project

### 6.2 Phase 2: Implement Scope Hierarchy

**New Fields:**

```python
class MemoryCreate(BaseModel):
    scope_path: str | None = Field(
        default=None,
        description="Hierarchical path: /project/x/agent/y/shared/z"
    )

    # Simplified - derive from scope_path
    access_level: AccessLevel = Field(default=AccessLevel.team)
```

**Scope Resolution:**

```
Query scope: /project/backend-dev/agent/researcher
Returns:
  - /shared/*              (public to project)
  - /project/backend-dev/* (project-scoped)
  - /agent/researcher/*   (agent-private, only if query from same agent)
```

### 6.3 Phase 3: Access Control & Audit

**Implementation:**

```python
class MemoryAccessPolicy:
    @staticmethod
    def can_read(memory: Memory, user: User, agent_id: str | None) -> bool:
        if memory.access_level == AccessLevel.public:
            return True
        if memory.access_level == AccessLevel.team:
            return user.project_id == memory.project_id
        if memory.access_level == AccessLevel.private:
            return memory.agent_id == agent_id
        return False
```

**Audit Log Model:**

```python
class MemoryAuditLog(BaseModel):
    action: AuditAction  # CREATE, READ, UPDATE, DELETE
    memory_id: str
    actor_id: str       # User or agent ID
    project_id: str
    timestamp: datetime
    result: bool
    details: dict
```

### 6.4 Phase 4: Frontend UI Updates

**New UI Components:**

1. **Memory Scope Selector**: Toggle between private/team/project
2. **Shared Memory View**: View all team memories
3. **Memory Audit Log Viewer**: See who accessed what
4. **Agent Memory Panel**: Per-agent memory overview

---

## 7. Implementation Roadmap

### Priority Order:

| Phase | Feature                    | Effort | Impact |
| ----- | -------------------------- | ------ | ------ |
| 1     | Add project_id to memories | Low    | High   |
| 2     | Implement scope hierarchy  | Medium | High   |
| 3     | Add access control         | Medium | High   |
| 4     | Add audit logging          | Medium | Medium |
| 5     | Frontend memory management | Medium | Medium |
| 6     | Cross-agent recall tools   | High   | High   |

### Migration Strategy:

1. **Backward Compatible**: Make agent_id optional initially
2. **Default to Team**: New memories default to project-scoped
3. **Migration Script**: Update existing memories with project_id from context
4. **Gradual Rollout**: Enable per-project

---

## 8. Conclusion

Eigent's current memory implementation provides a solid foundation with hybrid search and type-based organization. To support multi-agent collaboration, the key additions needed are:

1. **Project-based isolation** - Essential for multi-tenant/multi-project use
2. **Scope hierarchy** - Enables both private and shared memory patterns
3. **Access control** - Prevents unauthorized access to sensitive data
4. **Audit logging** - Provides traceability for compliance

The recommended approach follows CrewAI's scoped memory pattern, which provides a clean mental model while remaining compatible with the existing Qdrant-based storage.

---

## References

- [CrewAI Memory Documentation](https://github.com/crewaiinc/crewai/blob/main/docs/en/concepts/memory.mdx)
- [AutoGen Group Chat Guide](https://microsoft.github.io/autogen/docs/topics/group-chat)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/concepts/checkpointing/)
- Qdrant Documentation: https://qdrant.tech/documentation/

---

_Document Version: 1.0_
_Last Updated: 2026-03-08_
