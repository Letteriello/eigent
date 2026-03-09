---
name: research
description: Pesquisa automatizada de tópicos técnicos usando web search e NotebookLM. Cria cadernos de pesquisa organizados por tema. Use quando o usuário quiser pesquisar qualquer tópico relacionado ao projeto.
disable-model-invocation: true
user-invocable: true
---

# Research Skill

Pesquisa automaticamente qualquer tópico técnico e cria documentação organizada com fontes.

## Quando Usar

- Usuário quer pesquisar sobre qualquer tecnologia
- Precisa comparar soluções/técnicas
- Quer criar base de conhecimento organizada
- Precisa de pesquisa com fontes confiáveis

## Fluxo de Execução

### Passo 1: Extrair Tema de Pesquisa

Analise o pedido do usuário e extraia:

- **Tema principal**: O que pesquisar
- **Contexto**: Por que precisa saber
- **Escopo**: Quão profundo pesquisar

### Passo 2: Executar Pesquisas Web

Para cada tema, pesquise:

1. Tutoriais e documentações oficiais
2. Artigos técnicos e blog posts
3. Comparações e benchmarks
4. Repositórios GitHub relevantes
5. Discussões da comunidade (Reddit, Stack Overflow)

### Passo 3: Organizar Resultados

Crie estrutura de pasta em `docs/research/<tema>/`:

```
docs/research/
└── <tema-slugified>/
    ├── sources.md           # Todas as fontes coletadas
    ├── summary.md           # Resumo das descobertas
    ├── comparisons.md       # Comparações encontradas
    └── implementation.md    # Recomendações de implementação
```

### Passo 4: Criar Caderno NotebookLM (Opcional)

Se o usuário quiser usar NotebookLM:

1. Compile as melhores fontes
2. Crie caderno com título descritivo
3. Adicione fontes como referências

### Passo 5: Apresentar Resultados

Forneça ao usuário:

- Resumo executive das descobertas
- Lista de fontes mais relevantes
- Recomendações claras
- Próximos passos sugeridos

## Exemplos de Uso

```
/research o que são vector databases e quando usar
```

```
/research comparar React vs Vue para aplicações desktop Electron
```

```
/research melhores práticas de autenticação em FastAPI
```

## Dicas de Pesquisa

- Use termos em inglês para melhores resultados
- Inclua "2024" ou "2025" para resultados recentes
- Adicione "tutorial" para conteúdo educacional
- Adicione "github" para implementações
- Adicione "benchmark" para comparações de performance

## Integração com NotebookLM

Se o NotebookLM MCP estiver disponível, use-o para:

1. Criar cadernos automaticamente
2. Adicionar fontes aos cadernos existentes
3. Gerar resumos automáticos

Caso contrário, forneça instruções manuais para o usuário.
