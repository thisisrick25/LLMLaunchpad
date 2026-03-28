# Architecture

**Analysis Date:** 2026-03-28

## Pattern Overview

**Overall:** Hybrid client-server with Tauri desktop wrapper and modular backend services

**Key Characteristics:**
- Separation of concerns between frontend (Svelte/Tauri) and backend (Python/FastAPI)
- Event-driven communication via REST APIs and Server-Sent Events (SSE)
- Plugin-like architecture for model sources and inference backends
- Layered architecture with clear boundaries between presentation, application, and data layers
- Service-oriented design for llama.cpp and LiteLLM management

## Layers

**[Presentation Layer]:**
- Purpose: Handles UI rendering and user interactions
- Location: `app/src/`
- Contains: Svelte components, stores, API client, theme management
- Depends on: Shared types, API client
- Used by: User directly, Application layer

**[Application Layer]:**
- Purpose: Coordinates between frontend and backend, manages application state
- Location: `app/src/features/` (chat, models, services) and `app/src/shared/`
- Contains: Svelte stores, feature components, shared utilities
- Depends on: Presentation layer components, API client
- Used by: Presentation layer

**[API Layer (Backend)]:**
- Purpose: Exposes RESTful API for frontend communication
- Location: `server/src/llmlaunchpad/routes/`
- Contains: FastAPI route handlers for chat, conversations, models, control, status
- Depends on: Domain services (llama.py, models.py, etc.)
- Used by: Presentation layer via API client

**[Domain Layer]:**
- Purpose: Contains core business logic and service integrations
- Location: `server/src/llmlaunchpad/` (excluding routes/)
- Contains: Hardware detection, model management, llama.cpp control, database, config
- Depends on: External libraries (psutil, GPUtil, huggingface-hub, etc.)
- Used by: API layer

**[Infrastructure Layer]:**
- Purpose: External services and system interfaces
- Location: System-level (llama.binaries, LiteLLM, SQLite database)
- Contains: llama.cpp process, LiteLLM proxy, SQLite database files
- Depends on: System hardware and OS
- Used by: Domain layer

## Data Flow

**[Model Selection and Initialization]:**

1. User opens app → Frontend loads and displays UI
2. Frontend requests `/status` → Backend returns hardware info, config, service state
3. User browses models → Frontend calls `/models` → Backend scans local sources and returns GGUF files
4. User selects model → Frontend stores selection in Svelte store
5. User clicks Start → Frontend POSTs to `/services/start` with model and mode
6. Backend calculates GPU layers → Spawns llama-server process → Returns status
7. Backend begins logging to stdout/stderr → Frontend streams via SSE `/logs/stream`

**[Chat Interaction]:**

1. User types message → Frontend stores locally in chat store
2. Frontend POSTs to `/chat` with message and conversation ID → Backend validates
3. Backend forwards request to llama.cpp server (or LiteLLM in cloud mode)
4. Backend streams response tokens via SSE to frontend
5. Frontend displays tokens in real-time and stores in chat store
6. On completion, backend saves message to SQLite database
7. Frontend updates conversation list and search index

**[Service Control]:**

1. User clicks Stop → Frontend POSTs to `/services/stop`
2. Backend terminates llama.cpp and LiteLLM processes gracefully
3. Backend returns stopped status
4. Frontend updates UI to reflect stopped state

## Key Abstractions

**[Service Abstraction]:**
- Purpose: Represents a manageable backend service (llama.cpp, LiteLLM)
- Examples: `server/src/llmlaunchpad/llama.py`, `server/src/llmlaunchpad/litellm.py`
- Pattern: Service interface with start/stop/status methods, process management

**[Model Abstraction]:**
- Purpose: Represents a GGUF model with metadata and source information
- Examples: `server/src/llmlaunchpad/models.py`, `app/src/shared/types.ts` (LocalModel interface)
- Pattern: Data class with source attribution, file paths, Hugging Face metadata

**[Configuration Abstraction]:**
- Purpose: Manages application settings with platform-specific defaults
- Examples: `server/src/llmlaunchpad/config.py`, `app/src/shared/theme.ts`
- Pattern: Dataclass with validation, platform-aware path resolution, persistence

**[Hardware Abstraction]:**
- Purpose: Detects and reports system capabilities (GPU, CPU, RAM)
- Examples: `server/src/llmlaunchpad/hardware.py`
- Pattern: Platform-specific detection unified behind common interface

## Entry Points

**[Frontend Entry Point]:**
- Location: `app/src/main.ts`
- Triggers: Browser or Tauri runtime loads the application
- Responsibilities: Initialize Svelte app, set up stores, mount root component

**[Backend Entry Point]:**
- Location: `server/src/llmlaunchpad/main.py`
- Triggers: Direct execution (`python -m llmlaunchpad`) or Tauri CLI
- Responsibilities: Create FastAPI app, configure middleware, include routes, startup/shutdown handlers

**[Tauri Entry Point]:**
- Location: `app/src-tauri/src/main.rs`
- Triggers: Tauri runtime launches the desktop application
- Responsibilities: Set up Tauri window, configure frontend integration, handle system events

## Error Handling

**Strategy:** Hierarchical error handling with frontend display and backend logging

**Patterns:**
- Backend: HTTP exceptions with status codes, logged via Python logging
- Frontend: Error boundaries via Svelte try/catch, user-friendly error displays
- Network: Retry logic for transient failures, offline detection
- Process: Graceful shutdown of llama.cpp/LiteLLM on error or stop command
- Validation: Request/response validation via Pydantic (backend) and TypeScript (frontend)

## Cross-Cutting Concerns

**Logging:** Structured logging to files and real-time streaming via SSE
- Backend: Python logging module with file handlers
- Frontend: EventSource connection to `/logs/stream` endpoint
- Display: StatusBar component shows recent logs, collapsible panel for full view

**Validation:** Input validation at API boundaries
- Backend: Pydantic models for request/response validation
- Frontend: TypeScript interfaces, runtime validation where critical

**Authentication:** Not implemented (local-only application)
- Designed for local use only, no network exposure beyond localhost
- Future consideration: API key protection if exposing beyond localhost

**Configuration Management:** Platform-aware configuration with persistence
- Location: `~/.llmlaunchpad/config.json` (platform-specific expansion)
- Hot reload: Configuration changes detected and applied without restart
- Validation: Type checking and constraint validation on load/update

---

*Architecture analysis: 2026-03-28*