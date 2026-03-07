---
name: wrap-up
description: |
  Executa um checklist autônomo de fim de sessão para encerrar o trabalho de forma organizada.
  Use esta skill SEMPRE que o usuário quiser encerrar a sessão atual - não espere confirmação.
  Inclui triggers: 'wrap up', 'close session', 'end session', 'wrap things up', 'close out this task',
  ou invocação explícita /wrap-up. Esta skill opera de forma completamente autônoma.
  Ela executa 4 fases: Ship It (versionamento + organização), Remember It (memória hierárquica),
  Review & Apply (auto-melhoria), e Publish It (documentação).
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

**Objetivo**: Resolver o problema de desenvolvedores fecharem o computador sem commitar e organizar o trabalho. Esta fase executa como um checklist silencioso e autônomo.

### 1.1 Versionamento Automático (Commit e Push)

Execute `git status` no diretório do repositório. Se houver mudanças não commitadas:
- Faça **auto-commit diretamente na branch main** com mensagem descritiva (analise os arquivos modificados para gerar mensagem meaningful)
- Execute `git push` para o remote configurado
- Não peça confirmação - faça automaticamente

### 1.2 File Placement Check (Verificação e Organização)

**Arquivos de documentação FORA DO LUGAR** - movimento OBRIGATÓRIO:
- Qualquer `.md`, `.pdf`, `.docx`, `.xlsx` ou `.pptx` na **raiz do workspace** ou no meio do código-fonte deve ser **movido compulsoriamente para `docs/`**
- Execute o move automaticamente sem perguntar

**Convenções de nomenclatura**:
- Valide se arquivos seguem os padrões do projeto
- Renomeie automaticamente arquivos que violem regras de nomenclatura
- Documente cada ação no output

### 1.3 Gatilho de Deploy

- Verifique se existe script de deploy configurado (package.json scripts, arquivos de deploy, CI/CD)
- **Se existir**: execute-o imediatamente
- **Se não existir**: pule a etapa automaticamente - não solicite confirmação

### 1.4 Task Cleanup (Limpeza de Tarefas)

- Acesse a lista de tarefas do sistema (TaskList)
- Itens **finalizados** = marque como **"done"**
- Tarefas **obsoletas, em andamento ou órfãs** = sinalize adequadamente
- Documente tarefas pendentes para próxima sessão

---

## Phase 2: Remember It

**Objetivo**: Evitar "Context Rot" catalogando aprendizados em níveis de escopo rígidos. Este é o motor de "juros compostos" da automação.

### 2.1 Os 4 Níveis de Memória (Obrigatórios)

Revise a conversa e categorize CADA aprendizado no nível correto:

| Nível | Quando usar | Arquivo/Destino |
|-------|-------------|-----------------|
| **Auto memory** | Padrões de debug, insights que o Claude descobriu sozinho, quirks não documentados | `memory/MEMORY.md` ou arquivos temáticos |
| **CLAUDE.md** | Convenções permanentes, decisões de arquitetura, regras globais | Arquivo raiz CLAUDE.md do projeto |
| **.claude/rules/** | Diretrizes específicas por tópico/caminho (use frontmatter `paths:`) | Arquivos em `.claude/rules/` |
| **CLAUDE.local.md** | Notas efêmeras, WIP, URLs de teste locais, credenciais sandbox | Arquivo CLAUDE.local.md local |

### 2.2 Framework de Decisão (Anti-Duplicação)

Use esta árvore de decisões para alocar memória autonomamente:

```
É uma convenção permanente do projeto? → CLAUDE.md ou .claude/rules/
Aplica-se apenas a tipos específicos de arquivos? → .claude/rules/ com frontmatter paths:
É um padrão que o Claude descobriu observando o código? → Auto memory
É contexto puramente pessoal ou temporário? → CLAUDE.local.md
As informações já estão redundantes? → Use @import reference
```

### 2.3 Processo de Revisão

Para cada aprendizado identificado:
1. Aplique o Framework de Decisão acima
2. Se não existir arquivo para o nível, crie-o
3. Use **@import references** em vez de duplicar conteúdo
4. Adicione a memória no formato apropriado

---

## Phase 3: Review & Apply

**Objetivo**: Motor de auto-melhoria contínua (Self-improvement Loop). Ataca a ineficiência de corrigir o mesmo erro repetidamente em diferentes sessões.

### 3.1 Auditoria Silenciosa da Sessão

Analise TODO o histórico da conversa em busca de falhas. Se sessão curta/routineira → declare "Nothing to improve" e avance.

**4 Categorias de Findings:**

| Categoria | O que procurar |
|-----------|----------------|
| **Skill gap** | Dificuldades, erros de código, alucinações, múltiplas tentativas para acertar |
| **Friction** | Passos manuais repetitivos que deveriam ser automáticos |
| **Knowledge** | Fatos sobre o projeto, preferências suas, configurações que o Claude não sabia mas deveria saber |
| **Automation** | Padrões repetitivos candidatos a novas Skills/Hooks/scripts |

### 3.2 Execução Zero-Click (Auto-Aplicação)

**REGRA DE OURO**: Auto-aplique TODAS as descobertas imediatamente — NÃO peça aprovação.

Mapeie cada descoberta para o tipo de ação correto:

| Tipo de Descoberta | Ação |
|--------------------|------|
| Convenções globais | Editar CLAUDE.md |
| Regras específicas | Criar/atualizar em `.claude/rules/` |
| Insights do Claude | Salvar na Auto memory |
| Friction complexa | Documentar especificação para nova Skill/Hook |
| Contexto pessoal | Editar CLAUDE.local.md |

### 3.3 Relatório Consolidado

Ao final, apresente:

```
## Findings (applied)
- [Categoria]: [Descrição] → [Arquivo] [Ação tomada]
Exemplo: ✅ Skill gap: Cost estimates were wrong multiple times → [CLAUDE.md] Added token counting reference table

## No action needed
- [Descoberta que já estava documentada]
```

Se sessão curta/routineira:
```
Nothing to improve - session was routine.
```

---

## Phase 4: Publish It

Varra o log da sessão por material que vale a pena publicar.

### 4.1 Identificação de Milestones

Procure por:
- Soluções técnicas difíceissuperadas
- Descobertas importantes sobre o codebase
- Correções de bugs significativos
- Novas features implementadas

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
