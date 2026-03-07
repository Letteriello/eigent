# Design: Ícones Reais para MCP Tools

## Visão Geral

Substituir a bolinha verde placeholder por logos reais das empresas (Discord, Slack, Gmail, etc.) usando SVGs para melhor qualidade e reconhecibilidade.

## Problema Atual

- O componente `IntegrationList` usa uma imagem SVG simples (`ellipseIcon`) como placeholder
- O filtro CSS altera a cor (verde quando instalado), mas não representa visualmente o serviço
- O componente `MCPListItem` também usa uma bolinha verde (`bg-green-500`)
- Já existe `toolkitIcons.tsx` mas focado em tools internos, não em serviços MCP externos

## Solução Proposta

### 1. Biblioteca de Ícones

Criar `src/lib/mcpServiceIcons.tsx` com mapeamento de nomes de serviços para ícones:

```typescript
// Mapeamento de serviços para ícones Lucide ou componentes SVG
const mcpServiceIconMap: Record<string, LucideIcon | React.ComponentType> = {
  'Discord': DiscordIcon,      // SVG customizado
  'Slack': SlackIcon,          // SVG customizado
  'Gmail': GmailIcon,          // SVG customizado
  'Google Calendar': CalendarIcon,
  'Google Drive': DriveIcon,
  'Notion': NotionIcon,
  'LinkedIn': LinkedInIcon,
  // ... etc
};
```

### 2. Componente Reutilizável

Criar componente `MCPServiceIcon` em `src/components/MCPServiceIcon.tsx`:

- Props: `serviceName`, `size`, `className`
- Fallback: ícone genérico se não encontrar mapeamento
- Suporte a cores brand quando apropriado

### 3. Arquivos SVG

Adicionar logos em `src/assets/mcp/logos/`:
- discord.svg
- slack.svg
- gmail.svg
- notion.svg
- linkedin.svg
- google-calendar.svg
- google-drive.svg
- github.svg
- twitter.svg
- reddit.svg
- whatsapp.svg

### 4. Integração

**IntegrationList/index.tsx:**
- Substituir `<img src={ellipseIcon}>` por `<MCPServiceIcon serviceName={item.name} />`

**MCPListItem.tsx:**
- Substituir `<div className="bg-green-500 rounded-full">` por `<MCPServiceIcon serviceName={item.mcp_name} />`

### 5. Tratamento de Fallback

Se o serviço não tiver ícone customizado:
- Usar ícone genérico de ferramenta (Wrench ou Settings)
- Manter comportamento consistente com resto do app

## Decisões de Design

1. **SVGs inline vs arquivos**: Preferir SVGs inline para serviços principais (Discord, Slack, Gmail) para cores brand exatas
2. **Cores**: Serviços conhecidos devem manter suas cores brand
3. **Tamanho**: Padrão 20x20px, configurável via props
4. **Loading state**: Skeleton enquanto carrega (já existente)

## Servicos Suportados Inicialmente

| Serviço | Tipo Ícone | Prioridade |
|---------|-------------|------------|
| Discord | SVG brand | Alta |
| Slack | SVG brand | Alta |
| Gmail | SVG brand | Alta |
| Google Calendar | SVG brand | Alta |
| Notion | SVG brand | Alta |
| LinkedIn | SVG brand | Alta |
| Google Drive | SVG brand | Média |
| GitHub | SVG brand | Média |
| Twitter/X | SVG brand | Média |
| Reddit | SVG brand | Baixa |
| WhatsApp | SVG brand | Baixa |
| Outros | Lucide genérico | Fallback |

## Arquivos a Modificar

1. `src/lib/mcpServiceIcons.tsx` (novo)
2. `src/components/MCPServiceIcon.tsx` (novo)
3. `src/components/IntegrationList/index.tsx`
4. `src/pages/Connectors/components/MCPListItem.tsx`
5. `src/assets/mcp/logos/*.svg` (novos)

## Riscos e Mitigações

- **Risco**: Muitos serviços para mapear → **Mitigação**: Priorizar os mais populares, fallback para genérico
- **Risco**: Logos ocuparem muito espaço → **Mitigação**: SVGs otimizados, inline para principais
- **Risco**: Manutenção futura → **Mitigação**: Estrutura modular fácil de estender
