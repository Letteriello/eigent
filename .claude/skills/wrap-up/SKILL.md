---
name: wrap-up
description: |
  Executa um checklist autônomo de fim de sessão para encerrar o trabalho de forma organizada.
  Use esta skill quando o usuário quiser encerrar a sessão atual com versionamento automático,
  organização de memória e auto-melhoria. Inclui triggers: 'wrap up', 'close session', 'end session',
  'wrap things up', 'close out this task', ou invocação explícita /wrap-up.
  Esta skill opera autonomamente sem pedir aprovação do usuário em cada passo.
triggers:
  - wrap up
  - close session
  - end session
  - wrap things up
  - close out this task
  - /wrap-up
---

# Wrap-Up: Checklist de Encerramento de Sessão

Esta skill executa um checklist autônomo de fim de sessão em 4 fases, sem interromper o desenvolvedor com confirmações.

---

## Phase 1: Ship It

Execute esta fase primeiro para garantir que todo o trabalho esteja versionado e publicado.

### 1.1 Git Status e Versionamento

Execute `git status` para verificar mudanças não commitadas. Se houver mudanças:
- Faça auto-commit na branch main com mensagem descritiva
- Execute `git push` para o remote configurado

### 1.2 File Placement Check

Verifique se existem arquivos soltos que precisam ser organizados:

1. **Arquivos de documentação na raiz**: Arquivos `.md` ou `.pdf` soltos na raiz do projeto devem ser movidos para a pasta `docs/`
2. **Convenções de nomenclatura**: Valide que arquivos seguem os padrões do projeto

Para cada arquivo encontrado fora do lugar:
- Execute o move automaticamente
- Documente a ação no output

### 1.3 Deploy Script

Se existir script de deploy configurado no projeto (verifique package.json scripts ou arquivos de deploy):
- Execute o script de deploy

### 1.4 Task Cleanup

Se existir lista de tarefas (TaskList):
- Marque todos os itens com status 'completed' como 'done'
- Identifique tarefas pendentes e documente para próxima sessão

---

## Phase 2: Remember It

Revise os aprendizados da sessão e categorize a memória nos níveis apropriados.

### 2.1 Níveis de Memória

Revise a conversa e categorize aprendizados:

| Nível | Quando usar |
|-------|-------------|
| **Auto memory** | Padrões de debug, quirks do projeto, comportamentos inesperados |
| **CLAUDE.md** | Convenções permanentes, decisões de arquitetura, estruturas fixed |
| **.claude/rules/** | Instruções focadas em tópicos/caminhos específicos (use frontmatter `paths:`) |
| **CLAUDE.local.md** | Notas efêmeras, WIP, credenciais de sandbox, contexto local temporário |

### 2.2 Processo de Revisão

Para cada aprendizado identificado:
1. Determine o nível apropriado
2. Se não existir arquivo para esse nível, crie
3. Adicione a memória no formato apropriado

### 2.3 Auto Memory (se aplicável)

Se houver memórias novas para auto memory:
- Edite `C:\Users\gabri\.claude\projects\C--Users-gabri-Desktop-eigent\memory\MEMORY.md` ou crie arquivos temáticos

---

## Phase 3: Review & Apply

Analise a conversa em busca de padrões que podem ser melhorados.

### 3.1 Análise de Falhas

Procure por:

| Categoria | O que procurar |
|-----------|----------------|
| **Skill gaps** | Situações onde uma skill existiria mas não foi usada, ou onde uma skill seria útil |
| **Friction** | Passos manuais repetitivos que poderiam ser automatizados |
| **Knowledge** | Lacunas de contexto que causaram confusão ou retrabalho |

### 3.2 Auto-Aplicação de Correções

Para cada problema identificado:
1. Escreva a correção diretamente no arquivo apropriado (CLAUDE.md, rules, etc.)
2. Aplique imediatamente - não peça permissão

### 3.3 Output Consolidado

Ao final, apresente:

```
## Findings (applied)
- [Item 1]: Correção aplicada em [arquivo]
- [Item 2]: Correção aplicada em [arquivo]

## No action needed
- [Item que não requer ação]
```

---

## Phase 4: Publish It

Varra o log da sessão por material que vale a pena publicar.

### 4.1 Identificação de Milestones

Procure por:
- Soluções técnicas difíceissuperadas
- Descobertas importantes sobre o codebase
- Correções de bugs significativos
- Novasfeatures implementadas

### 4.2 Criação de Rascunho

Se houver material suficiente:
1. Crie um rascunho de postagem em formato apropriado
2. Salve na pasta de rascunhos (docs/drafts/ ou similar)
3. Inclua:
   - Título descritivo
   - Contexto do problema
   - Solução implementada
   - Código relevante (se aplicável)

### 4.3 Output

Se não houver material para publicar:
```
Nothing worth publishing from this session.
```

Se houver material:
```
Published: [caminho do arquivo]
```

---

## Formato de Saída

A skill deve produzir output estruturado mostrando o progresso em cada fase:

```
=== Wrap-Up Session ===
[Timestamp]

--- Phase 1: Ship It ---
✓ Git status checked
✓ Changes committed and pushed
✓ File placement validated
✓ Tasks cleaned up

--- Phase 2: Remember It ---
✓ Memories categorized:
  - [level]: [topic]

--- Phase 3: Review & Apply ---
[Findings applied / No action needed]

--- Phase 4: Publish It ---
[Publicação ou "Nothing worth publishing"]

=== Complete ===
```

---

## Notas de Implementação

- Esta skill executa de forma autônoma sem AskUserQuestion
- Todas as correções são aplicadas imediatamente
- O output é informativo mas não bloqueante
- Se uma fase falhar, continue para a próxima e documente o erro
