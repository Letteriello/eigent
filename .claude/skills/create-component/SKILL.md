---
name: create-component
description: Cria novo componente React com boilerplate padronizado
disable-model-invocation: true
---

# Create Component Skill

Cria um novo componente React com boilerplate遵循 o padrão do projeto Eigent.

## Quando Usar

Use esta skill quando:

- Usuário pede para criar um novo componente
- Precisa adicionar um novo componente React ao projeto

## Padrão do Componente

O componente deve seguir este template:

```typescript
// ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

import { cn } from '@/lib/utils';
import { memo } from 'react';

interface ComponentNameProps {
  className?: string;
  // adicionar props aqui
}

export const ComponentName = memo(function ComponentName({
  className,
  // desestruturar props aqui
}: ComponentNameProps) {
  return (
    <div className={cn('componentes classes aqui', className)}>
      {/* conteúdo */}
    </div>
  );
});
```

## Steps

1. **Pergunte o nome do componente e localização**
   - Ex: `src/components/ChatBox/MessageItem/MyComponent.tsx`

2. **Liste as props necessárias**
   - Identifique quais props o componente precisa

3. **Crie o arquivo com o template**
   - Use o padrão acima
   - Lembre-se de:
     - Incluir license header
     - Usar `cn()` de `@/lib/utils` para classes
     - Usar `memo()` para componentes que podem ser memoizados
     - Criar interface para props

4. **Exporte o componente**
   - Use export nomeado: `export const ComponentName`

## Exemplos de Uso

```
/create-component Button src/components/ui/Button.tsx
/create-component MyCard - props: title, description, onClick
```

## Notas

- Componentes de UI vão em `src/components/ui/`
- Componentes de feature vão em `src/components/<Feature>/`
- Use Radix UI quando possível para componentes base
- Siga convenções de nomenclatura do projeto
