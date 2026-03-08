# Agent Memory Patterns - Pesquisa 2026

**Data:** 2026-03-07
**Status:** Em Andamento
**Pesquisado por:** Claude Code com Skill Research

---

## 1. Arquiteturas de Memória para Agentes

### 1.1 Tipos de Memória

| Tipo           | Descrição                       | Uso no Eigent                   |
| -------------- | ------------------------------- | ------------------------------- |
| **Episodic**   | Memórias de eventos específicos | ✅ Implementado (fact, context) |
| **Semantic**   | Conhecimento generalizável      | ✅ Implementado (learned)       |
| **Working**    | Contexto imediato da tarefa     | ⚠️ Necessário implementar       |
| **Preference** | Preferências do usuário         | ✅ Implementado                 |

### 1.2 Padrões Arquiteturais

#### Memória Híbrida (BM25 + Vector)

- **Implementação Atual:** Busca híbrida com RRF (Reciprocal Rank Fusion)
- **Vantagem:** Combina busca textual e semântica
- **Referência:** `docs/plans/2026-03-07-memory-module-design.md`

#### Graph Memory

- Representa entidades e relações entre elas
- Útil para entender contexto complexo
- Ferramentas: Knowledge Graphs, Neo4j

#### Conversation Buffer

- Mantém histórico de conversas
- Implementação: LangChain ConversationBufferMemory

---

## 2. Implementações Populares

### 2.1 LangChain Memory Modules

| Módulo                             | Descrição                   | Adequado para Eigent |
| ---------------------------------- | --------------------------- | -------------------- |
| `ConversationBufferMemory`         | Buffer simples de conversas | ✅ Já usado          |
| `ConversationSummaryMemory`        | Resumo de conversas         | 🔄 Considerar        |
| `ConversationEntityMemory`         | Entidades identificadas     | 🔄 Considerar        |
| `ConversationKnowledgeGraphMemory` | Grafo de conhecimento       | 🔄 Futuras versões   |
| `VectorStoreRetrieverMemory`       | Memória vetorial            | ✅ Já implementado   |

### 2.2 AutoGen Patterns

- **Persistent Memory:** Armazenamento persistente entre sessões
- **User Proxy Memory:** Memória baseada em preferências do usuário
- **Group Chat Memory:** Memória compartilhada em conversas em grupo

### 2.3 CrewAI Memory

- **Agent Memory:** Memória individual por agente
- **Shared Memory:** Memória compartilhada entre agentes
- **Storage:** SQLite + Vector stores

---

## 3. Vector Stores - Comparação

| Store        | Prós                        | Contras              | Recomendado para  |
| ------------ | --------------------------- | -------------------- | ----------------- |
| **Qdrant**   | ✅ Rust, rápido, offline    | ❌ Menor ecossistema | ✅ Eigent (atual) |
| **Pinecone** | ✅ Gerenciado, escalável    | ❌ Pago, cloud-only  | Para escala       |
| **Weaviate** | ✅ Open source, multi-model | ❌ Complexidade      | Avançado          |
| **Chroma**   | ✅ Simples, local           | ❌ Menor escala      | Protótipos        |
| **pgvector** | ✅ PostgreSQL existente     | ❌ Performance       | Já tem Postgres   |

**Recomendação Atual:** Qdrant é a melhor escolha para o Eigent (já implementado).

---

## 4. Estratégias de Recuperação

### 4.1 Retrieval Patterns

```
Query → Pre-processing → [BM25 OR Vector] → RRF Fusion → Re-ranking → Results
```

### 4.2 Context Compression

- **LCEL (LangChain Expression Language):** Compacta contexto antes de enviar
- **Summarization:** Resume memórias antigas
- **Importance Filtering:** Filtra por score de importância

### 4.3 Temporal Awareness

- Memórias mais recentes têm peso maior
- Decay function para memórias antigas
- Implementação: `importance` field (0-1) já existente no design

---

## 5. Melhores Práticas

### 5.1 Design Patterns

1. **Separation of Concerns:** Backend (storage) vs Frontend (UI)
2. **Hybrid Search:** BM25 + Vector para melhor recall
3. **Importance Scoring:** Prioritize memórias importantes
4. **Type-based Filtering:** Diferentes tipos para diferentes contextos
5. **Lazy Loading:** Carregar memórias sob demanda

### 5.2 Recomendações para Eigent

| Melhoria             | Prioridade | Notas                                 |
| -------------------- | ---------- | ------------------------------------- |
| Working Memory       | Média      | Contexto imediato para tarefas        |
| Entity Extraction    | Média      | Identificar entidades automaticamente |
| Memory Summarization | Alta       | Resumir memórias antigas              |
| Memory Encryption    | Alta       | Proteger dados sensíveis              |
| Cross-agent Memory   | Baixa      | Memória compartilhada                 |

---

## 6. Fontes e Referências

### 6.1 Documentações Oficiais

- [LangChain Memory Docs](https://python.langchain.com/docs/modules/memory/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [AutoGen Memory Examples](https://microsoft.github.io/autogen/docs/topics/

### 6.2 Artigos e Tutoriais

- "Building Agentic Memory Systems" - Breve overview
- "Vector Search vs BM25" - Comparação técnica
- "RAG Patterns for Conversational AI" - Melhores práticas

### 6.3 Repositórios

- LangChain: `langchain-ai/langchain`
- AutoGen: `microsoft/autogen`
- CrewAI: `crewAIInc/crewai`

---

## 7. Próximos Passos

### Pesquisa Adicional

- [ ] Investigar Working Memory implementation
- [ ] Comparar ferramentas de entity extraction
- [ ] Estudar padrões de memory consolidation
- [ ] Avaliar opções de encryption at-rest

### Implementação

1. Adicionar Working Memory para contexto de tarefas
2. Implementar Memory Summarization para long-term
3. Adicionar Encryption para dados sensíveis

---

## 8. Evolução desta Pesquisa

| Data       | Atualização    | Responsável |
| ---------- | -------------- | ----------- |
| 2026-03-07 | Versão inicial | Claude Code |
|            |                |             |

---

_Esta pesquisa deve evoluir conforme novas descobertas. Use `/research-agent-memory` para continuar pesquisando._
