---
name: Session Memory Management
description: Regras para gerenciar memória de sessão e evitar Context Rot
paths: ['**/*']
---

# Session Memory Management

## Limites de Contexto

- Máximo: 80,000 tokens por sessão
- Alerta aos 60,000 tokens
- Ação obrigatória aos 75,000 tokens

## Estratégia de Pruning

Quando o contexto exceder 60k tokens:

1. Identificar informações redundantes
2. Consolidar conversas similares
3. Manter apenas decisões e resultados

## Triggers para Ação

- /prune-context: limpa contexto preservando decisões importantes
- Limite automático: quando > 75k tokens

## O que Preservar

- Decisões de arquitetura
- Configurações criadas/modificadas
- Bugs encontrados e soluções
- Referências importantes

## O que Pode Ser Descartado

- Repetições
- Explorações que não levaram a nada
- Conversas sobre problemas já resolvidos
