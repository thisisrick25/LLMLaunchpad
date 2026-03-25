# Contributing to LLMLaunchpad

Thank you for your interest in contributing!

## Getting Started

1. Follow the [README](README.md) to install prerequisites and set up the project
2. Fork the repository and create a feature branch

```bash
git checkout -b feature/your-feature-name
```

## Project Structure

```
LLMLaunchpad/
├── app/                          # Frontend (Svelte + Tauri)
│   ├── src/
│   │   ├── features/             # Feature modules
│   │   │   ├── chat/             # Chat UI and state
│   │   │   ├── models/           # Model management
│   │   │   └── services/         # Service controls
│   │   ├── shared/               # Shared utilities (api.ts, types.ts)
│   │   └── App.svelte
│   └── src-tauri/                # Tauri (Rust) config
│
├── server/                       # Backend (Python + FastAPI)
│   ├── src/llmlaunchpad/
│   │   ├── routes/               # API endpoints
│   │   ├── hardware.py           # Hardware detection
│   │   ├── llama.py              # llama.cpp management
│   │   ├── models.py             # Model scanning
│   │   └── database.py           # SQLite operations
│   └── tests/
│
├── scripts/                      # Build/install scripts
├── AGENTS.md                     # Project specification
└── ARCHITECTURE.md               # Technical architecture
```

## Coding Standards

### TypeScript/Svelte

- Use TypeScript for all new code
- Use Svelte stores for state management
- Keep components small and focused

```typescript
// Typed function
async function fetchModels(): Promise<LocalModel[]> {
  return await api.getModels();
}

// Reactive store
export const models = writable<LocalModel[]>([]);
```

### Python

- Use type hints for all functions
- Follow PEP 8
- Use async/await for I/O
- Document public functions

```python
async def get_hardware_info() -> HardwareInfo:
    """Detect and return hardware information."""
    ...
```

## Testing

```bash
# Backend (with venv activated)
cd server
pytest
pytest --cov=llmlaunchpad  # with coverage

# Frontend type checking
cd app
npm run check
```

### Manual Checklist

Before submitting:
- [ ] `npm run dev:server` starts without errors
- [ ] `npm run dev:app` starts without errors
- [ ] No TypeScript/Python type errors
- [ ] No browser console errors
- [ ] Affected features still work

## Pull Requests

### Branch Naming

- `feature/add-model-search` - New features
- `fix/chat-streaming-error` - Bug fixes
- `docs/update-readme` - Documentation
- `refactor/simplify-api` - Refactoring

### PR Title Format

Use conventional commits:
- `feat: add model search functionality`
- `fix: resolve chat streaming timeout`
- `docs: update installation instructions`
- `refactor: simplify hardware detection`

### PR Description

- What does this PR do?
- Why is this change needed?
- How was it tested?

## Issues

### Bug Reports

Include: description, steps to reproduce, expected vs actual behavior, environment (OS, Node/Python versions), error logs.

### Feature Requests

Include: description, use case, proposed solution, alternatives considered.

---

Thank you for contributing!
