# Coding Conventions

**Analysis Date:** 2026-03-28

## Naming Patterns

**Files:**
- TypeScript files: camelCase (e.g., `chat.ts`, `services.ts`)
- Svelte components: PascalCase (e.g., `ChatPanel.svelte`, `ModelSelector.svelte`)
- Python modules: snake_case (e.g., `hardware.py`, `database.py`)
- Configuration files: kebab-case or snake_case (e.g., `vite.config.ts`, `pyproject.toml`)

**Functions:**
- TypeScript: camelCase (e.g., `handleSubmit()`, `formatContent()`)
- Python: snake_case (e.g., `detect_hardware()`, `calculate_offload()`)

**Variables:**
- TypeScript: camelCase (e.g., `inputValue`, `messagesContainer`)
- Python: snake_case (e.g., `total_vram_gb`, `has_gpu`)

**Types/Interfaces:**
- TypeScript: PascalCase (e.g., `ChatMessage`, `HardwareInfo`)
- Python: PascalCase for classes (e.g., `LLMLaunchpad`, `Config`)

**Components:**
- Svelte components: PascalCase (e.g., `ChatPanel.svelte`, `StatusBar.svelte`)

## Code Style

**Formatting:**
- No ESLint or Prettier configuration detected in the codebase.
- Observed patterns in TypeScript files:
  - 2-space indentation
  - Semicolons used consistently
  - Single quotes for strings
  - Trailing commas in multiline objects/arrays
- Observed patterns in Python files:
  - 4-space indentation
  - No trailing whitespace
  - Lines limited to ~100 characters (PEP 8 influence)

**Linting:**
- No linting configuration files found (`.eslintrc*`, `.prettierrc*`, etc.)
- Code style appears to be maintained manually or via editor settings.

## Import Organization

**TypeScript:**
1. External dependencies (from 'package')
2. Absolute internal imports (from '$lib' or '$src' - not observed, using relative)
3. Relative internal imports (sorted by path depth)
   Example pattern seen in `ChatPanel.svelte`:
   ```typescript
   import { onMount, afterUpdate, tick } from 'svelte';
   import { chatStore, currentMessages, isStreaming, streamingContent, chatError } from './chat';
   import type { ChatMessage } from '../../shared/types';
   ```

**Python:**
1. Standard library imports
2. Third-party imports
3. Local application imports
   Example pattern seen in `main.py`:
   ```python
   import uvicorn
   from fastapi import FastAPI
   from . import __version__
   from .config import get_settings
   from .database import init_db
   ```

## Error Handling

**Patterns:**
- TypeScript: Use of try/catch for async operations, error stores in Svelte (e.g., `chatError` store)
- Python: Try/except blocks with logging, raising HTTPExceptions in FastAPI routes
- Example from `chat.ts` store: catching exceptions and setting error state
- Example from `routes/chat.py`: catching exceptions and returning 500 responses

## Logging

**Framework:** 
- No centralized logging framework detected.
- Use of `console.log`/`console.error` in TypeScript (observed in some files)
- Use of Python's `logging` module in backend (e.g., in `main.py` and `llama.py`)

**Patterns:**
- Backend: Logger instances per module (e.g., `logger = logging.getLogger(__name__)`)
- Frontend: Ad-hoc console logging for debugging

## Comments

**When to Comment:**
- No strict convention observed, but comments are used for:
  - Explaining complex logic (e.g., in `offload.py` for GPU layer calculations)
  - TODO/FIXME markers (seen in some files)
  - JSDoc/TSDoc style in TypeScript interfaces and functions

**JSDoc/TSDoc:**
- Used in shared TypeScript types file (`types.ts`) for interface descriptions
- Example: `/** * Shared TypeScript types for LLMLaunchpad. */`
- Some functions have JSDoc comments (e.g., in `api.ts`)

## Function Design

**Size:** 
- Functions tend to be small and focused (typically < 30 lines)
- Example: `handleSubmit()` in `ChatPanel.svelte` is 8 lines
- Example: `detect_hardware()` in `hardware.py` is ~20 lines

**Parameters:** 
- TypeScript: Interface objects for multiple related parameters (e.g., `StartRequest` interface)
- Python: Keyword arguments with defaults for optional parameters

**Return Values:** 
- TypeScript: Explicit return types for functions
- Python: Type hints for return values (observed in newer Python files)

## Module Design

**Exports:** 
- TypeScript: Named exports for functions, interfaces, and stores
- Example from `chat.ts`: exporting the chat store and derived stores
- Python: `__all__` not commonly used; public functions/classes imported directly

**Barrel Files:** 
- Not observed in TypeScript (no index.ts files exporting multiple modules)
- Python: `__init__.py` files used for package initialization, not as barrels