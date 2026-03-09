# Eigent - AI Cowork Desktop

Eigent is an open-source desktop application that enables you to build, manage, and deploy a custom AI workforce.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/eigent-ai/eigent.git
cd eigent

# Install dependencies
npm install
cd backend && uv sync && cd ..

# Development
npm run dev
```

## Commands

### Frontend (root)

| Command               | Description               |
| --------------------- | ------------------------- |
| `npm run dev`         | Start development server  |
| `npm run build`       | Build for production      |
| `npm run build:win`   | Build Windows installer   |
| `npm run build:mac`   | Build macOS installer     |
| `npm run build:linux` | Build Linux installer     |
| `npm run test`        | Run Vitest tests          |
| `npm run test:watch`  | Run tests in watch mode   |
| `npm run test:e2e`    | Run E2E tests             |
| `npm run type-check`  | TypeScript type check     |
| `npm run lint`        | Run ESLint                |
| `npm run lint:fix`    | Fix ESLint issues         |
| `npm run format`      | Format code with Prettier |
| `npm run storybook`   | Start Storybook           |

### Backend (./backend)

| Command                                | Description                 |
| -------------------------------------- | --------------------------- |
| `uv sync`                              | Install/update dependencies |
| `uv run uvicorn app.main:app --reload` | Run FastAPI server          |
| `uv run pytest`                        | Run Python tests            |
| `uv run ruff check --fix`              | Lint and fix code           |

## Architecture

```
eigent/
├── src/                      # React frontend (TypeScript)
│   ├── components/           # UI components
│   │   ├── ui/              # Base UI components (Radix + Tailwind)
│   │   ├── ChatBox/         # Chat interface
│   │   ├── WorkFlow/        # Workflow editor (React Flow)
│   │   ├── Terminal/       # Terminal emulator
│   │   └── ...
│   ├── store/               # Zustand stores
│   ├── hooks/               # React hooks
│   ├── lib/                # Utilities
│   ├── pages/              # Page components
│   ├── types/              # TypeScript types
│   └── App.tsx             # Main app entry
├── electron/                # Electron main process
│   ├── main/
│   │   ├── index.ts        # Main process entry
│   │   ├── install-deps.ts # Dependency installation
│   │   ├── update.ts       # Auto-update logic
│   │   └── utils/          # Utilities
│   └── preload/
│       └── index.ts        # Preload script
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── agent/          # AI agent implementation
│   │   │   ├── agent_model.py
│   │   │   ├── listen_chat_agent.py
│   │   │   ├── toolkit/    # Tool implementations
│   │   │   │   ├── browser_toolkit.py
│   │   │   │   ├── terminal_toolkit.py
│   │   │   │   └── ...
│   │   │   └── factory/    # Agent factories
│   │   ├── controller/     # API endpoints
│   │   ├── service/        # Business logic
│   │   ├── model/          # Pydantic models
│   │   └── main.py         # FastAPI entry
│   └── pyproject.toml
├── test/                    # Test files
│   └── unit/               # Unit tests
└── docs/                   # Documentation
```

## Key Files

| File                                  | Purpose                 |
| ------------------------------------- | ----------------------- |
| `src/App.tsx`                         | Main React application  |
| `src/main.tsx`                        | React entry point       |
| `electron/main/index.ts`              | Electron main process   |
| `electron/preload/index.ts`           | Preload bridge (IPC)    |
| `backend/app/main.py`                 | FastAPI application     |
| `backend/app/agent/agent_model.py`    | Agent model definitions |
| `backend/app/service/chat_service.py` | Chat orchestration      |
| `backend/app/agent/toolkit/*.py`      | Tool implementations    |

## Code Style

### TypeScript

- ESLint + Prettier configured
- Use `clsx` and `tailwind-merge` for className composition
- Radix UI for accessible components

### Python

- Ruff for linting and formatting
- Pydantic for data validation
- Async/await for I/O operations

## Gotchas

- **Build requirement**: Always run `npm run prebuild:deps` before building
- **Python version**: Requires Python 3.11 (see pyproject.toml)
- **Electron security**: Use `contextIsolation: true` and `nodeIntegration: false`
- **IPC**: Use preload script for secure renderer-main communication
- **Backend venv**: Located at `backend/.venv/`

## Testing

### Frontend

```bash
npm run test              # Unit tests
npm run test:e2e        # E2E tests with Playwright
npm run test:coverage   # Coverage report
```

### Backend

```bash
cd backend
uv run pytest           # Run all tests
uv run pytest -v        # Verbose output
```

## Environment

### Required

- Node.js 18-22
- Python 3.11
- uv (Python package manager)

### Optional

- GitHub CLI (for GitHub toolkit)
- Docker (for containerized development)

## MCP Servers ( Claude Code)

This project uses MCP servers. Configure in `.mcp.json`:

- `context7` - Documentation lookup
- `github` - GitHub operations

## Git Hooks

Husky is configured for pre-commit hooks. Run `npm install` to activate.
