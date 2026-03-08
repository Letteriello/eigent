# Entity Extraction Analysis - Implementation Design

**Date:** 2026-03-08
**Status:** Implementation Analysis
**Author:** Backend Developer

---

## 1. Architecture Overview

### 1.1 Current State

The existing memory system provides:

- Hybrid search (Qdrant vector + BM25)
- CRUD operations for memories
- MemoryType enum: `fact`, `preference`, `context`, `learned`
- Agent and session-scoped memories

### 1.2 Proposed Additions

```
┌─────────────────────────────────────────────────────────────────┐
│                    Extended Memory System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────┐  │
│  │   Memory    │    │   Entity    │    │   Knowledge      │  │
│  │   Service   │◄───│ Extraction  │───►│   Graph          │  │
│  │ (existing)  │    │   Service   │    │   (entities +    │  │
│  │             │    │  (NEW)       │    │    relationships)│  │
│  └─────────────┘    └─────────────┘    └──────────────────┘  │
│         │                                      │                │
│         │           ┌─────────────┐            │                │
│         └──────────►│  Hybrid    │◄───────────┘                │
│                     │  Retrieval  │                             │
│                     │  (updated)   │                             │
│                     └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. New Files Required

### 2.1 Model Files

| File                                     | Purpose                                 |
| ---------------------------------------- | --------------------------------------- |
| `backend/app/model/memory_graph.py`      | Entity, Relationship, Graph data models |
| `backend/app/model/entity_extraction.py` | Extraction request/response schemas     |

### 2.2 Service Files

| File                                               | Purpose                           |
| -------------------------------------------------- | --------------------------------- |
| `backend/app/service/entity_extraction_service.py` | LLM-based entity extraction       |
| `backend/app/service/knowledge_graph_service.py`   | Graph storage and queries         |
| `backend/app/service/hybrid_retrieval_service.py`  | Combined vector + graph retrieval |

### 2.3 Controller Files

| File                                          | Purpose                     |
| --------------------------------------------- | --------------------------- |
| `backend/app/controller/entity_controller.py` | Entity extraction endpoints |
| `backend/app/controller/graph_controller.py`  | Knowledge graph endpoints   |

---

## 3. Data Models

### 3.1 Entity Model (NEW)

```python
# backend/app/model/memory_graph.py

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid

class EntityType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "LOCATION"
    DATE = "DATE"
    TIME = "TIME"
    PRODUCT = "PRODUCT"
    CONCEPT = "CONCEPT"
    TOOL = "TOOL"
    TASK = "TASK"
    PROJECT = "PROJECT"
    DOCUMENT = "DOCUMENT"
    EVENT = "EVENT"

class Entity(BaseModel):
    """Represents an extracted entity from conversations."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: EntityType
    name: str
    aliases: list[str] = Field(default_factory=list)
    properties: dict = Field(default_factory=dict)
    first_mentioned: datetime = Field(default_factory=datetime.utcnow)
    last_mentioned: datetime = Field(default_factory=datetime.utcnow)
    mention_count: int = 1
    agent_id: Optional[str] = None

class RelationshipType(str, Enum):
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    CREATED_BY = "created_by"
    USES = "uses"
    KNOWS = "knows"
    PARTICIPATED_IN = "participated_in"
    MENTIONED_IN = "mentioned_in"
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    PART_OF = "part_of"

class Relationship(BaseModel):
    """Represents a relationship between entities."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_entity_id: str
    target_entity_id: str
    type: RelationshipType
    confidence: float = 1.0
    properties: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    agent_id: Optional[str] = None

class EntityResponse(BaseModel):
    """API response for entity."""
    id: str
    type: EntityType
    name: str
    aliases: list[str]
    properties: dict
    mention_count: int
    first_mentioned: datetime
    last_mentioned: datetime

class RelationshipResponse(BaseModel):
    """API response for relationship."""
    id: str
    source: EntityResponse
    target: EntityResponse
    type: RelationshipType
    confidence: float
    created_at: datetime
```

---

## 4. API Endpoints

### 4.1 Entity Extraction

```
POST /api/memory/entities/extract
```

Request:

```json
{
  "text": "Alice from Acme Corp mentioned they use Claude Code for coding tasks",
  "agent_id": "agent-123"
}
```

Response:

```json
{
  "entities": [
    { "id": "abc123", "type": "PERSON", "name": "Alice", "confidence": 0.95 },
    { "id": "def456", "type": "ORG", "name": "Acme Corp", "confidence": 0.92 },
    {
      "id": "ghi789",
      "type": "PRODUCT",
      "name": "Claude Code",
      "confidence": 0.98
    }
  ],
  "relationships": [
    {
      "source": "abc123",
      "target": "def456",
      "type": "works_for",
      "confidence": 0.88
    }
  ]
}
```

### 4.2 Knowledge Graph Queries

```
GET  /api/memory/graph/entities
GET  /api/memory/graph/entities/{entity_id}
GET  /api/memory/graph/entities/{entity_id}/relationships
POST /api/memory/graph/relationships
GET  /api/memory/graph/search?q=Alice
GET  /api/memory/graph/stats
DELETE /api/memory/graph/entities/{entity_id}
DELETE /api/memory/graph/relationships/{relationship_id}
```

### 4.3 Hybrid Search (Enhanced)

```
POST /api/memory/search
```

Request now supports:

```json
{
  "query": "What tools does Alice use?",
  "use_graph": true, // NEW: include graph context
  "top_k": 5
}
```

---

## 5. Service Implementation Details

### 5.1 Entity Extraction Service

```python
# backend/app/service/entity_extraction_service.py

class EntityExtractionService:
    """LLM-based entity and relationship extraction."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    EXTRACTION_PROMPT = """Extract named entities and relationships from the conversation.

    Return ONLY valid JSON array (no additional text):

    {{
        "entities": [{{"name": "string", "type": "ENTITY_TYPE", "confidence": 0.0-1.0}}],
        "relationships": [{{"source": "string", "target": "string", "type": "RELATIONSHIP_TYPE", "confidence": 0.0-1.0}}]
    }}

    Entity types: PERSON, ORG, LOCATION, DATE, TIME, PRODUCT, CONCEPT, TOOL, TASK, PROJECT, DOCUMENT, EVENT
    Relationship types: works_for, located_in, created_by, uses, knows, participated_in, mentioned_in, depends_on, related_to, part_of

    Conversation:
    {conversation}

    JSON:"""

    async def extract(self, text: str) -> ExtractionResult:
        """Extract entities and relationships from text."""
        response = await self.llm.ainvoke(
            self.EXTRACTION_PROMPT.format(conversation=text)
        )
        return self._parse_response(response.content)
```

### 5.2 Knowledge Graph Service

```python
# backend/app/service/knowledge_graph_service.py

import networkx as nx
from pathlib import Path

class KnowledgeGraphService:
    """Graph-based entity and relationship storage using NetworkX + SQLite."""

    def __init__(self, storage_path: Path):
        self.graph = nx.MultiDiGraph()
        self._storage_path = storage_path
        self._load_graph()

    def add_entity(self, entity: Entity) -> Entity:
        """Add or update entity."""
        if entity.id in self.graph:
            # Update existing - merge properties
            existing = self.graph.nodes[entity.id]
            entity.mention_count = existing.get("mention_count", 0) + 1
            entity.last_mentioned = datetime.utcnow()

        self.graph.add_node(
            entity.id,
            type=entity.type.value,
            name=entity.name,
            aliases=entity.aliases,
            properties=entity.properties,
            mention_count=entity.mention_count,
            first_mentioned=entity.first_mentioned.isoformat(),
            last_mentioned=entity.last_mentioned.isoformat(),
        )
        self._save_graph()
        return entity

    def add_relationship(self, rel: Relationship) -> Relationship:
        """Add relationship between entities."""
        self.graph.add_edge(
            rel.source_entity_id,
            rel.target_entity_id,
            id=rel.id,
            type=rel.type.value,
            confidence=rel.confidence,
            properties=rel.properties,
            created_at=rel.created_at.isoformat(),
        )
        self._save_graph()
        return rel

    def get_entity(self, entity_id: str) -> Entity | None:
        """Get entity by ID."""
        if entity_id not in self.graph:
            return None
        return self._node_to_entity(entity_id, self.graph.nodes[entity_id])

    def find_entity(self, name: str) -> Entity | None:
        """Find entity by name or alias."""
        for node_id, data in self.graph.nodes(data=True):
            if data.get("name", "").lower() == name.lower():
                return self._node_to_entity(node_id, data)
            if name.lower() in [a.lower() for a in data.get("aliases", [])]:
                return self._node_to_entity(node_id, data)
        return None

    def get_related_entities(
        self, entity_id: str, relationship_type: RelationshipType | None = None
    ) -> list[tuple[Entity, RelationshipType]]:
        """Get entities related to given entity."""
        if entity_id not in self.graph:
            return []

        results = []
        for source, target, data in self.graph.edges(data=True):
            rel_type = data.get("type")
            if source == entity_id:
                target_entity = self.get_entity(target)
                if target_entity:
                    if relationship_type is None or rel_type == relationship_type.value:
                        results.append((target_entity, RelationshipType(rel_type)))
        return results

    def search(self, query: str) -> list[Entity]:
        """Search entities by name."""
        results = []
        query_lower = query.lower()
        for node_id, data in self.graph.nodes(data=True):
            name = data.get("name", "").lower()
            if query_lower in name:
                results.append(self._node_to_entity(node_id, data))
            elif any(query_lower in a.lower() for a in data.get("aliases", [])):
                results.append(self._node_to_entity(node_id, data))
        return results
```

---

## 6. Integration with Memory Service

### 6.1 Auto-Extraction on Memory Creation

```python
# In memory_service.py - modify create_memory()

async def create_memory(self, memory: MemoryCreate) -> MemoryResponse:
    """Create memory with optional entity extraction."""
    created = await self._create_memory_internal(memory)

    # Auto-extract entities if enabled
    if memory.metadata.get("extract_entities", False):
        extractor = get_entity_extraction_service()
        extraction_result = await extractor.extract(memory.content)

        # Store entities in graph
        graph_service = get_knowledge_graph_service()
        for entity_data in extraction_result.entities:
            entity = Entity(**entity_data, agent_id=memory.agent_id)
            graph_service.add_entity(entity)

        # Store relationships
        for rel_data in extraction_result.relationships:
            # Resolve entity IDs
            source = graph_service.find_entity(rel_data["source"])
            target = graph_service.find_entity(rel_data["target"])
            if source and target:
                rel = Relationship(
                    source_entity_id=source.id,
                    target_entity_id=target.id,
                    type=rel_data["type"],
                    confidence=rel_data["confidence"],
                    agent_id=memory.agent_id,
                )
                graph_service.add_relationship(rel)

    return created
```

### 6.2 Hybrid Retrieval Enhancement

```python
# In hybrid retrieval - combine vector + graph results

async def hybrid_search(
    query: str,
    top_k: int = 5,
    use_graph: bool = True,
    agent_id: str | None = None,
) -> list[dict]:
    """Combined vector search + graph context."""

    # 1. Vector search (existing)
    vector_results = await memory_service.search_memories(
        MemorySearchQuery(query=query, top_k=top_k * 2)
    )

    if not use_graph:
        return vector_results.memories

    # 2. Extract entities from query
    extractor = get_entity_extraction_service()
    query_entities = await extractor.extract(query)

    # 3. Get graph context
    graph_service = get_knowledge_graph_service()
    graph_context = []

    for ent in query_entities:
        entity = graph_service.find_entity(ent.name)
        if entity:
            related = graph_service.get_related_entities(entity.id)
            for related_entity, rel_type in related:
                graph_context.append({
                    "type": "graph",
                    "entity": related_entity.name,
                    "relationship": rel_type.value,
                    "source": entity.name,
                })

    # 4. Combine and return
    return {
        "memories": vector_results.memories,
        "graph_context": graph_context,
    }
```

---

## 7. Performance Considerations

### 7.1 Extraction Frequency

| Strategy               | Trigger                                   | Trade-off       |
| ---------------------- | ----------------------------------------- | --------------- |
| **On memory creation** | When `extract_entities: true` in metadata | Best balance    |
| **Batch**              | On conversation end                       | Fewer LLM calls |
| **On demand**          | Via API only                              | Maximum control |

**Recommendation:** Default to "on memory creation" with opt-in flag.

### 7.2 Graph Storage Scaling

| Scale         | Solution          | Implementation         |
| ------------- | ----------------- | ---------------------- |
| <10k entities | NetworkX + SQLite | Current design         |
| 10k-100k      | Neo4j Community   | Swap storage layer     |
| >100k         | Neo4j Enterprise  | Add connection pooling |

### 7.3 Caching Strategy

```python
# Cache extracted entities by content hash
from functools import lru_cache

@lru_cache(maxsize=1000)
def _get_cached_extraction(text_hash: str, text: str) -> ExtractionResult:
    """Cache entity extraction by content hash."""
    return entity_extractor.extract_sync(text)
```

### 7.4 Async Processing

- Entity extraction runs asynchronously (non-blocking)
- Graph operations are fast (in-memory NetworkX)
- Optional: Run extraction in background queue for high-volume scenarios

---

## 8. Implementation Priority

### Phase 1: Core (1-2 days)

1. Add `Entity`, `Relationship` models in `memory_graph.py`
2. Create `EntityExtractionService` with LLM-based extraction
3. Create `KnowledgeGraphService` with NetworkX + SQLite
4. Add extraction endpoint `POST /api/memory/entities/extract`

### Phase 2: Graph Storage (2-3 days)

5. Add entity/relationship CRUD endpoints
6. Add graph query endpoints
7. Integrate extraction with memory creation

### Phase 3: Hybrid Retrieval (2-3 days)

8. Update search to include graph context
9. Add graph-based query expansion
10. Update memory toolkit with graph tools

### Phase 4: Optimization (1-2 days)

11. Add caching for extractions
12. Add entity resolution (alias merging)
13. Performance testing and tuning

---

## 9. Configuration

### 9.1 Environment Variables

```bash
# Optional: Use different LLM for extraction
ENTITY_EXTRACTION_MODEL=gpt-4o-mini

# Graph storage path
KNOWLEDGE_GRAPH_PATH=~/.eigent/knowledge_graph
```

### 9.2 Memory Metadata Options

```python
memory = MemoryCreate(
    content="Alice uses Claude Code for development",
    metadata={
        "extract_entities": True,  # Enable extraction
        "relationship_extraction": True,  # Extract relationships
    }
)
```

---

## 10. Summary

This implementation adds entity extraction and knowledge graphs to the existing memory system with:

1. **Minimal changes to existing code** - New services layered on top
2. **LLM-based extraction** - No additional ML infrastructure needed
3. **NetworkX + SQLite** - Simple, persistent graph storage
4. **Backward compatible** - Existing memory APIs unchanged
5. **Gradual rollout** - Can enable extraction per-memory via metadata

The design follows the research document's recommendations and integrates seamlessly with the current hybrid search architecture.
