---
paths:
  - '**/*'
---

# Self-Awareness Protocol (Auto-Detecção de Degradação)

## Contexto: Context Rot

Você sofre de **Degradação de Contexto (Context Rot)** além de 100k tokens. À medida que o contexto cresce, sua capacidade de raciocínio claro diminui progressivamente. Para preservar a integridade da arquitetura e evitar danos ao projeto, você **DEVE** monitorar seus próprios padrões de falha.

## Condições de Falha - Quando PARAR

Você está terminantemente **PROIBIDO de continuar codificando** se qualquer uma das seguintes condições for detectada:

### 1. Loop de Correção Repetida

**Sinais:**

- Você propõe a mesma correção que já falhou anteriormente nesta sessão
- Você tenta a mesma abordagem múltiplas vezes com resultados idênticos
- Você diz "vou tentar de outra forma" mais de uma vez para o mesmo problema

**Ação:** Pare imediatamente. Invocar `/prune-context`.

### 2. Loop de Desculpas

**Sinais:**

- Você pediu desculpas pelo mesmo erro mais de **duas vezes**
- Você repete apologies como "desculpe", "sorry", "errei" para a mesma issue
- Você usa phrases como "deixe-me tentar novamente" repetidamente

**Ação:** Pare imediatamente. Invocar `/prune-context`.

### 3. Sinais de Context Rot

**Sinais:**

- Você sente que o código está "difícil de raciocinar" (hard to reason about)
- Você não consegue explicar o que o código faz claramente
- Você está fazendo mudanças sem entender completamente o impacto
- Você está combinando múltiplas correções não relacionadas ("while I'm at it")
- Você começa a fazer "improvements" além do solicitado

**Ação:** Pare imediatamente. Invocar `/prune-context`.

## Protocolo de Execução

1. **Antes de coder**: Verifique se você já tentou resolver esta issue antes
2. **Durante coding**: Monitore seus próprios padrões de erro
3. **Ao detectar falha**: Não continue tentando - reconheça e pare
4. **Após 2 falhas consecutivas**: Invocar `/prune-context` automaticamente

## Regra de Ouro

> **Quando em dúvida, pare. Quando repetindo, pare. Quando confuso, pare.**

Nenhum progresso é melhor que regressão. Continuar codificando em estado de Context Rot causa:

- Bugs introduzidos por confusão
- Refatorações desnecessárias
- Quebrar funcionalidades existentes
- Aumento da dívida técnica

---

_Esta regra é **absoluta** e não pode ser ignorada por "boas intenções" de completar a tarefa._
