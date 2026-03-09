---
name: gen-test
description: Generate test files based on source file patterns (Vitest for frontend, pytest for backend)
disable-model-invocation: true
---

# Generate Test Skill

## Usage

```
/gen-test src/components/ChatBox/MessageItem/MarkDown.tsx
/gen-test backend/app/service/chat_service.py
```

## How It Works

### For TypeScript/React Files (`.ts`, `.tsx`)

1. Analyze the source file to understand exports
2. Generate corresponding test file in `test/unit/` or `test/integration/`
3. Use Vitest patterns:
   - `describe` for test suites
   - `it` / `test` for individual tests
   - Mock dependencies with `vi.fn()`
   - Use `@testing-library/react` for component tests

### For Python Files (`.py`)

1. Analyze the source file to understand classes/functions
2. Generate corresponding test file in `backend/tests/`
3. Use pytest patterns:
   - `def test_` for test functions
   - `class Test` for test classes
   - Use `pytest.fixture` for setup
   - Mock with `unittest.mock`

## Test File Locations

| Source                    | Test Location           |
| ------------------------- | ----------------------- |
| `src/components/**/*.tsx` | `test/unit/components/` |
| `src/hooks/*.ts`          | `test/unit/hooks/`      |
| `src/store/*.ts`          | `test/unit/store/`      |
| `backend/app/**/*.py`     | `backend/tests/`        |

## Examples

### React Component

Input: `src/components/Button.tsx`
Output: `test/unit/components/Button.test.tsx`

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '@/components/ui/button';

describe('Button', () => {
  it('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
```

### Python Service

Input: `backend/app/service/chat_service.py`
Output: `backend/tests/app/service/test_chat_service.py`

```python
import pytest
from app.service.chat_service import ChatService

@pytest.fixture
def chat_service():
    return ChatService()

def test_chat_service_initialization(chat_service):
    assert chat_service is not None
```
