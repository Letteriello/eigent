---
name: research-agent-memory
description: Pesquisa automaticamente as melhores práticas, arquiteturas e configurações para recursos de memória de agentes de IA, criando cadernos de pesquisa no NotebookLM. Use quando o usuário quiser melhorar ou implementar recursos de memória no projeto.
disable-model-invocation: true
user-invocable: true
---

# Research Agent Memory

Esta skill pesquisa automaticamente as melhores práticas e arquiteturas para memória de agentes de IA, criando cadernos de pesquisa no NotebookLM.

## Quando Usar

- Usuário quer melhorar o recurso de memória do projeto
- Precisa entender padrões de arquitetura de memória para agentes
- Quer documentar fontes e artigos sobre o tema
- Precisa de pesquisa iterativa que evolui com o tempo

## Fluxo de Execução

### Passo 1: Definir Tema de Pesquisa

O tema deve ser específico e relacionado à memória de agentes de IA. Exemplos:

- "Agent memory architectures patterns"
- "Context window optimization techniques"
- "Vector database for AI agent memory"
- "Retrieval augmented generation for agents"

### Passo 2: Executar Pesquisa Web

Pesquise os seguintes tópicos relacionados ao tema:

1. **Arquiteturas de Memória**:
   - Episodic memory patterns
   - Semantic memory structures
   - Working memory vs long-term memory
   - Memory consolidation strategies

2. **Implementações Populares**:
   - LangChain memory modules
   - AutoGen memory patterns
   - CrewAI memory implementations
   - OpenAI assistant memory

3. **Bancos de Dados e embeddings**:
   - Vector stores (Pinecone, Weaviate, Chroma)
   - Embedding models for memory
   - Similarity search optimization

4. **Padrões de Recuperação**:
   - Retrieval augmented generation
   - Memory retrieval strategies
   - Context compression techniques

### Passo 3: Criar Caderno no NotebookLM

Para cada pesquisa significativa, crie um caderno no NotebookLM com as fontes encontradas.

Use o MCP NotebookLM se disponível, ou forneça instruções para o usuário criar manualmente.

### Passo 4: Documentar Descobertas

Crie um arquivo de documentação em `docs/research/` com:

- Título da pesquisa
- Fontes encontradas (links)
- Principais descobertas
- Recomendações para implementação
- Próximos passos para pesquisa adicional

## Estrutura de Saída

```
docs/research/
└── agent-memory/
    ├── 2024-01-initial-research.md    # Primeira pesquisa
    ├── 2024-02-vector-stores.md       # Pesquisa sobre vector stores
    └── summary.md                     # Consolidated findings
```

## Pesquisa Inicial Sugerida

Se o usuário quiser melhorar a memória do projeto,.execute estas pesquisas:

1. **Arquitetura de Memória**:
   - "agent memory architecture patterns 2024"
   - "long-term memory for AI agents"

2. **Implementação Técnica**:
   - "LangChain memory types tutorial"
   - "ChromaDB vs Pinecone vs Weaviate"

3. **Padrões de Recuperação**:
   - "semantic search for agent context"
   - "RAG patterns for conversational AI"

## Exemplo de Uso

```
/research-agent-memory melhorar memória do projeto agente
```

Irá:

1. Pesquisar arquiteturas de memória para agentes
2. Encontrar implementações populares (LangChain, AutoGen, etc.)
3. Comparar soluções de vector stores
4. Criar caderno de pesquisa no NotebookLM
5. Documentar recomendações em docs/research/

## Notas

- Esta skill requer acesso à internet para pesquisa
- Use o NotebookLM MCP se disponível para criar cadernos automaticamente
- Armazene sempre as fontes para referência futura
- A pesquisa deve evoluir iterativamente conforme novas necessidades surgem
