# Design: Módulo de Memória Persistente para Agentes

**Data:** 2026-03-07
**Status:** Aprovado
**Stack:** FastAPI + Qdrant + React + TypeScript

---

## 1. Visão Geral

Implementar um módulo de memória persistente que permite aos agentes AI lembrar informações importantes entre sessões. O sistema armazenará preferências, fatos aprendidos, histórico de interações e contexto.

### Escopo

- **Backend:** FastAPI com Qdrant para busca vetorial + SQLite para metadados
- **Frontend:** Página React para gerenciamento de memória
- **Integração:** Ferramentas para agentes acessarem memória

---

## 2. Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐│
│  │ Memory.tsx │  │ Preferences │  │  Memory Settings UI          ││
│  └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────────┘│
└─────────┼─────────────────┼───────────────────────┼───────────────┘
          │                 │                       │
          ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    MEMORY API LAYER                             ││
│  │  POST /api/memory/{agent_id}     - Salvar memória             ││
│  │  GET  /api/memory/{agent_id}     - Listar memórias            ││
│  │  GET  /api/memory/{agent_id}/search - Busca híbrida           ││
│  │  DELETE /api/memory/{id}          - Remover memória           ││
│  │  PUT  /api/memory/{id}           - Atualizar memória          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│  ┌────────────────────────────┼───────────────────────────────────┐│
│  │              MEMORY SERVICE LAYER                              ││
│  │  MemoryRecorder | MemoryRetriever | MemoryManager             ││
│  └────────────────────────────┼───────────────────────────────────┘│
│                               │                                      │
│  ┌────────────────────────────┼───────────────────────────────────┐│
│  │            STORAGE LAYER (Qdrant + SQLite)                    ││
│  │  Qdrant: embeddings + texto | SQLite: metadados               ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Modelos de Dados

### Enum: MemoryType

```python
class MemoryType(str, Enum):
    FACT = "fact"           # Fatos aprendidos
    PREFERENCE = "preference"  # Preferências do usuário
    CONTEXT = "context"    # Contexto de trabalho
    LEARNED = "learned"    # Aprendizados gerais
```

### Modelo: AgentMemory

```python
class AgentMemory(BaseModel):
    id: UUID
    agent_id: str
    content: str                    # Texto da memória
    memory_type: MemoryType         # Tipo de memória
    embedding: list[float]          # Vetor (1536 dim - OpenAI ada-002)
    importance: float = 0.5         # 0-1, para recall prioritário
    created_at: datetime
    updated_at: datetime
    metadata: dict                   # Tags, source, etc.
```

---

## 4. API Endpoints

| Método | Endpoint                           | Descrição                          |
| ------ | ---------------------------------- | ---------------------------------- |
| POST   | `/api/memory/{agent_id}`           | Criar nova memória                 |
| GET    | `/api/memory/{agent_id}`           | Listar todas as memórias do agente |
| GET    | `/api/memory/{agent_id}/search`    | Busca híbrida (query param)        |
| GET    | `/api/memory/{id}`                 | Obter memória específica           |
| PUT    | `/api/memory/{id}`                 | Atualizar memória                  |
| DELETE | `/api/memory/{id}`                 | Deletar memória                    |
| DELETE | `/api/memory/agent/{agent_id}/all` | Limpar todas as memórias           |

---

## 5. Busca Híbrida

### Algoritmo: Reciprocal Rank Fusion (RRF)

1. **BM25** (texto): Busca por palavras-chave
2. **Vector** (semântica): Busca porsimilaridade de embeddings
3. **Fusão RRF**: Combina resultados com ranking

```
Query → BM25 Search → Scores ─┐
                              ├→ RRF → Final Ranking → Top K
Query → Vector Search → Scores ─┘
```

### Parâmetros de Busca

- `query`: Texto da busca
- `limit`: Número de resultados (default: 5)
- `memory_type`: Filtrar por tipo (opcional)
- `min_importance`: Filtrar por importância mínima

---

## 6. Integração com Agentes

### Ferramentas do Agente

```python
# memory_toolkit.py
class MemoryToolkit:
    """Ferramentas para agentes acessarem memória"""

    def save_memory(content: str, memory_type: MemoryType, importance: float)
    def search_memories(query: str, limit: int, memory_type: MemoryType)
    def delete_memory(memory_id: str)
    def list_memories(memory_type: MemoryType | None)
```

### Context Injection

```python
def get_context_for_agent(agent_id: str, task: str) -> str:
    """Recupera memórias relevantes para injetar no prompt"""
    memories = memory_service.search(
        query=task,
        hybrid=True,
        limit=5
    )
    return format_as_context(memories)
```

---

## 7. Frontend (React)

### Página: Memory.tsx

- Lista de memórias com filtros por tipo
- Busca com resultados em tempo real
- CRUD completo de memórias
- Indicador de importância visual

### Store: memoryStore.ts (Zustand)

```typescript
interface MemoryState {
  memories: AgentMemory[];
  loading: boolean;
  searchResults: AgentMemory[];
  fetchMemories: (agentId: string) => Promise<void>;
  searchMemories: (agentId: string, query: string) => Promise<void>;
  createMemory: (memory: CreateMemoryDTO) => Promise<void>;
  updateMemory: (id: string, data: UpdateMemoryDTO) => Promise<void>;
  deleteMemory: (id: string) => Promise<void>;
}
```

---

## 8. Dependências

### Novas dependências (Python)

- `rank-bm25` - Algoritmo BM25 para busca textual

### Dependências existentes utilizadas

- `qdrant-client` - Banco de vetores
- `openai` - Embeddings
- `fastapi` - API REST

---

## 9. Configuração

### Variáveis de Ambiente

```env
# Memory Service
MEMORY_EMBEDDING_MODEL=text-embedding-ada-002
MEMORY_EMBEDDING_DIM=1536
MEMORY_QDRANT_PATH=~/.eigent/qdrant
```

---

## 10. Roadmap de Implementação

### Fase 1: Backend Core

- [ ] Modelos de dados (Pydantic)
- [ ] Service layer (CRUD)
- [ ] Controller (endpoints REST)
- [ ] Integração Qdrant básica

### Fase 2: Busca Híbrida

- [ ] Implementação BM25
- [ ] Fusão RRF
- [ ] Busca por tipo

### Fase 3: Frontend

- [ ] Memory.tsx (UI completa)
- [ ] memoryStore.ts (Zustand)
- [ ] Integração API

### Fase 4: Integração Agentes

- [ ] MemoryToolkit para agentes
- [ ] Context injection
- [ ] Testes de integração

---

## 11. Decisões de Design

| Decisão                       | Justificativa                                                       |
| ----------------------------- | ------------------------------------------------------------------- |
| Qdrant + SQLite               | Qdrant para vetores, SQLite para metadados (já temos qdrant-client) |
| Embeddings OpenAI ada-002     | Já usado no RAG existente, dimensão 1536                            |
| Busca híbrida (BM25 + Vector) | Melhor precisão combinando busca textual e semântica                |
| Coleções por agente           | Isolamento natural e segurança                                      |
| Importância 0-1               | Controle granular sobre quais memórias priorizar                    |

---

## 12. Riscos e Mitigações

| Risco                   | Mitigação                                        |
| ----------------------- | ------------------------------------------------ |
| Latência alta em buscas | Cache em memória + índices otimizados            |
| Custo de embeddings     | Batch processing + cache de embeddings           |
| Dados sensíveis         | Criptografia em repouso + isolamento por projeto |
| Escala                  | Paginação + limites configuráveis                |
