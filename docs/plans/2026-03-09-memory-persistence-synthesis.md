# Arquitetura de Memória Persistente - Síntese Final

**Data**: 2026-03-09
**Status**: ✅ Fase 1 Completa, Fase 2/3 Em Andamento

---

## Sumário Executivo

O sistema de memória do Eigent foi analisado e mejorado através de um brainstorming colaborativo com 15+ especialistas. A principal decisão arquitetural foi manter o Qdrant local como storage principal, resolver gaps críticos de persistência, e implementar um ciclo de vida completo para as memórias. As implementações da Fase 1 estão completas, resolvendo o problema central de memórias não persistirem entre sessões.

---

## Fases de Implementação

### ✅ Fase 1 - Quick Wins (Completa)

**Objetivo**: Resolver gaps críticos para funcionamento básico

| Tarefa | Responsável | Status |
|--------|-------------|--------|
| Carregar memórias do Qdrant ao iniciar | coordenador-synthesis | ✅ |
| Conectar toolkit ao service | coordenador-synthesis | ✅ |
| Adicionar lifecycle states | coordenador-synthesis | ✅ |

**Implementações Realizadas**:

1. **memory_service.py**
   - Adicionado `_load_memories_from_storage()` que carrega todas as memórias do Qdrant ao iniciar o serviço
   - Garante que o dict `_memories` é populado a partir do storage persistente

2. **memory_toolkit.py**
   - Adicionadas 4 novas ferramentas:
     - `list_memories` - Listar memórias com filtros
     - `update_memory` - Atualizar conteúdo/importância (com verificação de ownership)
     - `delete_memory` - Deletar memória (com verificação de ownership)
     - `get_memory_stats` - Estatísticas de uso
   - Validação de segurança: agentes só podem modificar suas próprias memórias

3. **enums.py**
   - Novo enum `MemoryStatus` com estados: pending, new, active, stale, archived, deleted

4. **memory.py**
   - Campo `status: MemoryStatus` adicionado ao modelo `MemoryResponse`

---

### 🔄 Fase 2 - Em Andamento

**Objetivo**: Lifecycle automático, métricas e backup

| Tarefa | Responsável | Status |
|--------|-------------|--------|
| Lifecycle automático | @especialista-ciclo | 🔄 |
| Métricas | @especialista-metricas | 🔄 |
| Backup | @especialista-backup | 🔄 |

**Features Planejadas**:

1. **Lifecycle Automático**
   - Transições: recall → reactivate
   - Auto-cleanup diário
   - Campo `last_accessed_at`

2. **Métricas**
   - search_stats (latência, hit rate)
   - orphan_count (memórias sem agente)
   - by_lifecycle_state (contagem por estado)

3. **Backup**
   - Export/import JSON
   - Backup automático (a cada 50 memórias + diário)
   - Rotação: 7 diários + 4 semanais

---

### ⏳ Fase 3 - Pendente

**Objetivo**: Segurança, multi-agente e UI

| Tarefa | Responsável | Status |
|--------|-------------|--------|
| Criptografia AES-256-GCM | @especialista-seguranca | ⏳ |
| Multi-agente scopes | @especialista-multiagente | ⏳ |
| UI de gerenciamento | @designer-ui | ⏳ |

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  ┌─────────────────┐    ┌────────────────────────────────┐  │
│  │   Zustand Store │    │   IndexedDB (Dexie.js)        │  │
│  │  (estado app)   │    │  - cache de leituras         │  │
│  └────────┬────────┘    └────────────┬───────────────────┘  │
└───────────┼──────────────────────────┼──────────────────────┘
            │                          │
            ▼                          ▼
┌───────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              MemoryService                                   │   │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐   │ │
│  │  │  _memories      │◀──▶│   QdrantStorage             │   │ │
│  │  │  (in-memory)    │    │   ~/.eigent/memory_storage │   │ │
│  │  │  ★ RECARREGAR  │    │   (persiste vetores)        │   │ │
│  │  └─────────────────┘    └─────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
            │                        │
            ▼                        ▼
┌───────────────────────────────────────────────────────────────────┐
│              ELECTRON MAIN PROCESS                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  app.getPath('userData')                                    │   │
│  │  ├── memory_cache.json (cache local)                       │   │
│  │  └── electron-store (configurações)                        │   │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

---

## Decisões de Arquitetura

| Decisão | Justificativa |
|---------|---------------|
| **Qdrant local** | Já implementado, persiste offline em `~/.eigent/memory_storage` |
| **Cache Electron** | JSON em `userData` para dados frequentes |
| **Ciclo de 6 estados** | Pending → New → Active → Stale → Archived → Deleted |
| **IndexedDB para frontend** | Maior capacidade que localStorage |
| **JSON+gzip para backup** | Formato simples, compressão eficiente |
| **Access levels** | private / team / public (para multi-agente) |

---

## Limitações Conhecidas

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| Qdrant corrompido | Alto | Backup antes de consolidações |
| Deduplicação destrutiva | Médio | Criarmerged memory (Fase 2) |
| Fernet vs AES-256-GCM | Alto | Migrar na Fase 3 |
| Sem multi-agente scopes | Médio | Implementar na Fase 3 |

---

## Próximos Passos Recomendados

### Imediato (Esta Sprint)
1. Testar a Fase 1: criar memória → fechar app → reabrir → verificar persistência
2. Finalizar lifecycle automático (Fase 2)
3. Implementar API de backup

### Curto Prazo (Próxima Sprint)
1. Dashboard de métricas
2. Cache IndexedDB no frontend
3. Testes de recovery

### Médio Prazo (Este Mês)
1. Migrar Fernet → AES-256-GCM real
2. Implementar scopes multi-agente
3. Melhorar UI com 4 abas

---

## Referências

- Documento de design: `docs/plans/2026-03-07-memory-module-design.md`
- Implementação inicial: `docs/plans/2026-03-07-memory-module-implementation.md`
- Código fonte: `backend/app/service/memory_service.py`
- Toolkit: `backend/app/agent/toolkit/memory_toolkit.py`

---

*Documento gerado pelo coordinator-synthesis após brainstorming colaborativo com 15+ especialistas.*
