# Entity Extraction and Knowledge Graph Memory for AI Agents

**Date:** 2026-03-08
**Status:** Research Complete
**Researcher:** Claude Code

---

## 1. Overview

This document covers entity extraction (NER), relationship extraction, and knowledge graph-based memory storage for AI agents. These technologies enable agents to understand not just *what* was discussed, but *who*, *what*, and *how* things relate to each other.

---

## 2. Entity Extraction (NER)

### 2.1 What is NER?

Named Entity Recognition (NER) is the task of identifying and classifying named entities in text into predefined categories such as:
- **People** (PERSON): names of individuals
- **Organizations** (ORG): companies, agencies, institutions
- **Locations** (GPE): cities, countries, regions
- **Dates/Times** (DATE, TIME): temporal expressions
- **Products** (PRODUCT): software, tools, objects
- **Events** (EVENT): conferences, meetings, incidents

### 2.2 Entity Extraction Approaches

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **Rule-based** | Pattern matching, regex | Fast, no training needed | Limited coverage |
| **Statistical ML** | CRF, HMM models | Good accuracy | Requires training data |
| **Deep Learning** | BiLSTM-CRF, Transformers | State-of-the-art accuracy | Computationally expensive |
| **LLM-based** | Prompt engineering | No training, flexible | Token limits, cost |

### 2.3 Recommended Tools for Entity Extraction

#### Python Libraries

| Library | Use Case | Integration |
|---------|----------|-------------|
| **spaCy** | Production NER | Fast, pre-trained models |
| **HuggingFace Transformers** | Fine-tuned NER | Access to latest models |
| **Stanford NER** | Academic/Research | Robust, well-tested |
| **Prodigy** | Training custom NER | Active learning workflow |

#### LLM-based Extraction (Recommended for Agents)

For agent applications, using the LLM itself for entity extraction is often the best approach:

```python
# Example: Extract entities using the agent's LLM
EXTRACT_ENTITIES_PROMPT = """Extract entities from the conversation.
Return a JSON list with: type, name, mentions, confidence.

Categories: PERSON, ORGANIZATION, LOCATION, DATE, PRODUCT, CONCEPT

Conversation:
{conversation_history}

Entities:"""

def extract_entities(llm, conversation: str) -> list[dict]:
    """Extract entities using LLM."""
    response = llm.invoke(EXTRACT_ENTITIES_PROMPT.format(
        conversation_history=conversation
    ))
    return parse_json_response(response)
```

### 2.4 Relationship Extraction

Beyond identifying entities, understanding *how* they relate is crucial:

```python
# Relationship types for agent memory
RELATIONSHIP_TYPES = [
    "works_for",        # PERSON -> ORG
    "located_in",       # ENTITY -> LOCATION
    "created_by",       # PRODUCT -> PERSON/ORG
    "uses",             # PERSON -> TOOL/SOFTWARE
    "knows",            # PERSON -> PERSON
    "participated_in",  # PERSON -> EVENT
    "mentioned_in",     # CONCEPT -> DOCUMENT
    "depends_on",       # CONCEPT -> CONCEPT
]
```

---

## 3. Knowledge Graphs for Agents

### 3.1 Graph-Based Memory Architecture

Knowledge graphs store information as nodes (entities) and edges (relationships):

```
    [User: Alice] ----works_for----> [Org: Acme Corp]
         |                                    |
         | mentioned_in                        | created
         v                                    v
    [Project: Alpha] <----created_by---- [Tool: Eigent]
         |
         | uses
         v
    [Task: Migration]
```

### 3.2 Benefits for Agent Memory

| Benefit | Description |
|---------|-------------|
| **Relationship Understanding** | Knows how entities relate, not just what's said |
| **Infer новые связи** | Can deduce implicit relationships |
| **Efficient Querying** | Graph queries faster than full text search for relationships |
| **Explainability** | Can trace why a memory is relevant |

### 3.3 Graph Database Options

| Database | Pros | Cons | Best For |
|----------|------|------|----------|
| **Neo4j** | Mature, Cypher query language, cloud options | Memory-heavy | Production deployments |
| **NetworkX** (in-memory) | Python native, easy | Not persistent | Prototyping, small data |
| **ArangoDB** | Multi-model (graph + document) | Less mature | Flexibility needs |
| **SQLite + graph** | Simple, portable | Limited graph features | Simple agent memory |
| **DuckDB** | Fast analytical queries | Not graph-native | Hybrid workloads |

### 3.4 Recommended: Hybrid Approach

For Eigent, combining graph with existing vector storage is optimal:

```
┌─────────────────────────────────────────────────┐
│              Agent Memory System                │
├─────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌───────────────────────┐ │
│  │   Vector DB  │    │   Graph (Neo4j/      │ │
│  │   (Qdrant)   │    │   NetworkX)          │ │
│  │              │    │                       │ │
│  │ - Semantic   │    │ - Entities           │ │
│  │   search    │    │ - Relationships      │ │
│  │ - Full-text │    │ - Graph traversal   │ │
│  │   (BM25)    │    │                       │ │
│  └──────────────┘    └───────────────────────┘ │
│          │                    │                │
│          └────────┬───────────┘                │
│                   ▼                             │
│           ┌──────────────┐                      │
│           │   Unified   │                      │
│           │   Retrieval │                      │
│           │   Layer     │                      │
│           └──────────────┘                      │
└─────────────────────────────────────────────────┘
```

---

## 4. Implementation Approaches

### 4.1 LangChain Entity Memory

LangChain provides `ConversationEntityMemory` that tracks entities:

```python
from langchain.memory import ConversationEntityMemory
from langchain.memory.entity import SQLiteEntityStore

# Initialize entity memory with persistence
entity_memory = ConversationEntityMemory(
    llm=llm,
    entity_store=SQLiteEntityStore(persist_path="entities.db"),
    k=5,  # Number of entities to track
)

# The memory automatically:
# - Extracts entities from messages
# - Summarizes entity information
# - Includes relevant entities in context
```

### 4.2 Custom Implementation (Recommended for Eigent)

Given Eigent's existing architecture, a custom implementation provides better control:

```python
# backend/app/model/memory_graph.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "LOC"
    DATE = "DATE"
    PRODUCT = "PRODUCT"
    CONCEPT = "CONCEPT"
    TOOL = "TOOL"
    TASK = "TASK"

class Entity(BaseModel):
    id: str
    type: EntityType
    name: str
    aliases: list[str] = []
    properties: dict = {}
    first_mentioned: datetime
    last_mentioned: datetime
    mention_count: int = 1

class Relationship(BaseModel):
    id: str
    source_id: str  # Entity ID
    target_id: str  # Entity ID
    type: str       # works_for, uses, etc.
    properties: dict = {}
    confidence: float = 1.0
    created_at: datetime

class KnowledgeGraph(BaseModel):
    entities: dict[str, Entity] = {}  # id -> Entity
    relationships: list[Relationship] = []
    
    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity
        
    def add_relationship(self, rel: Relationship) -> None:
        self.relationships.append(rel)
        
    def get_entity(self, name: str) -> Optional[Entity]:
        for entity in self.entities.values():
            if entity.name.lower() == name.lower():
                return entity
            if name.lower() in [a.lower() for a in entity.aliases]:
                return entity
        return None
    
    def get_related_entities(self, entity_id: str, relation_type: Optional[str] = None) -> list[Entity]:
        related_ids = []
        for rel in self.relationships:
            if rel.source_id == entity_id:
                if relation_type is None or rel.type == relation_type:
                    related_ids.append(rel.target_id)
        return [self.entities[eid] for eid in related_ids if eid in self.entities]
```

### 4.3 Entity Extraction Service

```python
# backend/app/service/entity_extraction.py

from typing import list
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
import json
import hashlib

class ExtractedEntity(BaseModel):
    name: str
    type: str
    confidence: float = 1.0
    mentions: list[str] = []

class EntityExtractor:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
    EXTRACTION_PROMPT = """Extract named entities from the following text.
Return ONLY a valid JSON array with no additional text.

Format: [{{"name": "entity name", "type": "TYPE", "confidence": 0.0-1.0}}]

Valid types: PERSON, ORGANIZATION, LOCATION, DATE, PRODUCT, CONCEPT, TOOL, TASK

Text:
{text}

JSON:"""
    
    def extract(self, text: str) -> list[ExtractedEntity]:
        """Extract entities from text using LLM."""
        response = self.llm.invoke(
            self.EXTRACTION_PROMPT.format(text=text)
        )
        
        try:
            data = json.loads(response.content)
            return [ExtractedEntity(**item) for item in data]
        except json.JSONDecodeError:
            return []
    
    def extract_from_conversation(self, messages: list[dict]) -> list[ExtractedEntity]:
        """Extract entities from conversation history."""
        all_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])
        return self.extract(all_text)
```

---

## 5. Query Patterns

### 5.1 Graph Traversal Queries

```python
# Find all entities related to a specific entity
def get_entity_context(graph: KnowledgeGraph, entity_name: str) -> dict:
    entity = graph.get_entity(entity_name)
    if not entity:
        return {"entity": None, "relationships": [], "context": []}
    
    # Get all relationships
    related = graph.get_related_entities(entity.id)
    
    # Build context
    context = {
        "entity": entity,
        "related_entities": [
            {"entity": e, "type": e.type}
            for e in related
        ],
        "relationship_summary": summarize_relationships(graph, entity.id)
    }
    
    return context

# Find path between two entities (for understanding connections)
def find_connection(graph: KnowledgeGraph, entity1: str, entity2: str) -> list[str]:
    """Find shortest path between two entities using BFS."""
    from collections import deque
    
    start = graph.get_entity(entity1)
    end = graph.get_entity(entity2)
    
    if not start or not end:
        return []
    
    queue = deque([(start.id, [start.id])])
    visited = {start.id}
    
    while queue:
        current, path = queue.popleft()
        
        if current == end.id:
            return path
        
        for rel in graph.relationships:
            if rel.source_id == current and rel.target_id not in visited:
                visited.add(rel.target_id)
                queue.append((rel.target_id, path + [rel.target_id]))
    
    return []
```

### 5.2 Hybrid Retrieval (Graph + Vector)

```python
async def hybrid_retrieve(
    query: str,
    vector_store,  # Qdrant
    knowledge_graph: KnowledgeGraph,
    top_k: int = 5
) -> list[dict]:
    """Combine vector search with graph expansion."""
    
    # 1. Vector search
    vector_results = await vector_store.similarity_search(query, k=top_k)
    
    # 2. Extract entities from query
    extractor = EntityExtractor(llm)
    query_entities = extractor.extract(query)
    
    # 3. Expand with graph results
    graph_contexts = []
    for entity in query_entities:
        graph_entity = knowledge_graph.get_entity(entity.name)
        if graph_entity:
            related = knowledge_graph.get_related_entities(graph_entity.id)
            graph_contexts.extend([
                {"type": "graph", "content": f"{entity.name}: {e.name}"}
                for e in related
            ])
    
    # 4. Combine and rank
    all_results = [
        {"type": "memory", "content": r.page_content, "score": r.score}
        for r in vector_results
    ] + graph_contexts
    
    return all_results[:top_k]
```

---

## 6. Integration with Eigent's Architecture

### 6.1 Changes Required

| Component | Change | Priority |
|-----------|--------|----------|
| `memory_service.py` | Add graph storage layer | High |
| `memory_model.py` | Add Entity, Relationship models | High |
| New `entity_extraction.py` | Entity extraction service | High |
| `memory_toolkit.py` | Add graph query tools | Medium |
| Frontend `memoryStore.ts` | Display entity relationships | Low |

### 6.2 Data Model Updates

```python
# Add to backend/app/model/memory.py

class MemoryType(str, Enum):
    FACT = "fact"
    CONTEXT = "context"
    LEARNED = "learned"
    ENTITY = "entity"        # NEW: Extracted entity
    RELATIONSHIP = "relationship"  # NEW: Entity relationship

class Memory(BaseModel):
    id: str
    content: str
    type: MemoryType
    importance: float = 0.5
    # NEW: Graph-specific fields
    entity_id: Optional[str] = None    # Link to graph entity
    source_memory_id: Optional[str] = None  # Original memory
    created_at: datetime
    updated_at: datetime
```

### 6.3 API Endpoints

```
POST /api/memory/entities/extract     # Extract entities from text
POST /api/memory/graph/query          # Query knowledge graph
GET  /api/memory/graph/entity/{id}   # Get entity details
GET  /api/memory/graph/relationships # List relationships
```

---

## 7. Performance Considerations

### 7.1 Extraction Frequency

| Strategy | When | Pros | Cons |
|----------|------|------|------|
| **On every message** | Real-time | Always current | More LLM calls |
| **On conversation end** | Batch | Fewer calls | Delayed extraction |
| **On memory creation** | Hybrid | Balances both | Medium complexity |

**Recommendation:** Extract entities on memory creation for new facts/context.

### 7.2 Graph Storage Scaling

- **Small scale (<10k entities):** NetworkX in-memory + SQLite persistence
- **Medium scale:** Neo4j Community Edition
- **Large scale:** Neo4j Enterprise or GraphDB

### 7.3 Caching Strategy

```python
# Cache extracted entities to avoid re-extraction
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_entities(text_hash: str, text: str) -> list[ExtractedEntity]:
    """Cache entity extraction results."""
    return entity_extractor.extract(text)
```

---

## 8. Benefits for Eigent

### 8.1 Enhanced Memory Retrieval

With entity extraction and knowledge graphs, Eigent can:

1. **Understand who** - Track people mentioned in conversations
2. **Understand what** - Identify tools, projects, tasks
3. **Understand relationships** - Know how entities connect

### 8.2 Example Improvements

| Scenario | Without Graph | With Graph |
|----------|---------------|------------|
| User asks "What tools did Alice use?" | Must search all memories | Direct graph query: Alice -> uses -> Tool |
| User asks "What's related to Project X?" | Text similarity | Graph traversal: Project X -> related entities |
| User asks "Who worked on this?" | Keyword search | Graph: Project -> created_by -> Person |

### 8.3 Context Continuity

Knowledge graphs provide:
- **Cross-conversation memory** - Remembers relationships across sessions
- **Inference** - Can deduce new relationships
- **Explainability** - Can show *why* a memory is relevant

---

## 9. Implementation Roadmap

### Phase 1: Core (Week 1-2)
- [ ] Add Entity, Relationship models
- [ ] Create entity extraction service
- [ ] Integrate extraction with memory creation

### Phase 2: Storage (Week 3-4)
- [ ] Add graph storage layer
- [ ] Implement basic graph queries
- [ ] Add relationship extraction

### Phase 3: Integration (Week 5-6)
- [ ] Update retrieval to use hybrid (vector + graph)
- [ ] Add graph query tools to agent toolkit
- [ ] Update frontend to show entity relationships

### Phase 4: Optimization (Week 7+)
- [ ] Add caching for entity extraction
- [ ] Implement graph analytics
- [ ] Add entity resolution (linking aliases)

---

## 10. References

### Documentation
- [LangChain Entity Memory](https://python.langchain.com/docs/modules/memory/how_to/entity_summary_memory/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/)
- [spaCy NER](https://spacy.io/usage/linguistic-features#named-entities)

### Libraries
- **NetworkX:** Python graph library (https://networkx.org/)
- **py2neo:** Neo4j Python binding (https://py2neo.org/)
- **珍珠 (Spacy):** Industrial-strength NLP

### Research Papers
- "Neural Named Entity Recognition" - Survey of NER approaches
- "Knowledge Graphs in NLP" - Survey of KG applications

---

## 11. Summary

Entity extraction and knowledge graphs significantly enhance agent memory by:

1. **Structured understanding** - Beyond raw text, agents understand entities and relationships
2. **Better retrieval** - Graph queries can find relevant context traditional search misses
3. **Inference capability** - Can deduce new relationships from existing data
4. **Cross-session continuity** - Remembers connections across conversations

**Recommendation:** Implement incremental approach starting with LLM-based entity extraction, then add graph storage layer, and finally integrate hybrid retrieval.

---

*Document created as part of Eigent agent memory research.*
*See also: `docs/research/agent-memory/initial-research.md`*
