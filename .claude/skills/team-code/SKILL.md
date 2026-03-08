---
name: team-code
description: Cria um time de agentes especializados para trabalhar em paralelo no projeto Eigent
user-invocable: true
---

# Team Code Skill

Use esta skill quando quiser trabalhar com múltiplos agentes em paralelo.

## Como Usar

Quando o usuário pedir para implementar algo grande ou múltiplas tarefas:

1. **Analise as tarefas** - Identifique se o trabalho pode ser dividido em partes independentes
2. **Crie o team** - Use TeamCreate com `team_name` e `description`
3. **Defina os teammates** - Escolha baseado na tarefa:
   - `frontend-dev` - Para trabalho em React/TypeScript (src/)
   - `backend-dev` - Para trabalho em Python/FastAPI (backend/)
   - `code-reviewer` - Para revisar código
   - `debugger` - Para investigar bugs
4. **Assign tarefas** - Use TaskCreate para criar tarefas e TaskUpdate para assignar
5. **Coordene** - Use SendMessage para comunicação entre agentes

## Exemplos de Uso

```
/team-code implementar tela de login e API correspondente
```

```
/team-code revisar PR #142 em paralelo (segurança, performance, testes)
/team-code investigar bug de conexão em paralelo (3 teorias diferentes)
/team-code adicionar 3 novas integrações MCP (Discord, Slack, Gmail)
```

## Estrutura do Team

Para trabalho em código:
- 1-2 frontend devs (se envolver frontend)
- 1-2 backend devs (se envolver backend)
- 1 code reviewer

Para debugging:
- 1-3 debuggers testando hipóteses diferentes

## Limitações

- Agent teams são experimentais (precisa `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
- Cada teammate tem seu próprio context window
- Comunicação via SendMessage ou task list compartilhada
