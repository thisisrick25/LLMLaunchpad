# Codebase Structure

**Analysis Date:** 2026-03-28

## Directory Layout

```
LLMLaunchpad/
├── .planning/                  # GSD planning documents (auto-generated)
├── app/                        # Svelte + Tauri frontend (web + desktop)
│   ├── src/                    # Application source code
│   │   ├── features/           # Feature-specific components and stores
│   │   ├── shared/             # Shared utilities, types, API client
│   │   ├── App.svelte          # Root application component
│   │   ├── main.ts             # Application entry point
│   │   └── app.css             # Global styles
│   └── src-tauri/              # Tauri desktop wrapper
│       ├── src/                # Rust backend for Tauri
│       │   └── main.rs         # Tauri application entry point
│       ├── tauri.conf.json     # Tauri configuration
│       ├── capabilities/       # Tauri v2 permission definitions
│       │   └── main.json       # Main window capabilities
│       ├── icons/              # Application icons for all platforms
│       └── Cargo.toml          # Rust project dependencies
├── server/                     # Python backend service
│   ├── src/                    # Backend source code
│   │   └── llmlaunchpad/       # Main application package
│   │       ├── __init__.py     # Package initializer
│   │       ├── main.py         # FastAPI application entry point
│   │       ├── config.py       # Configuration management
│   │       ├── database.py     # SQLite + FTS5 database layer
│   │       ├── hardware.py     # GPU/CPU/RAM detection
│   │       ├── llama.py        # llama.cpp process management
│   │       ├── litellm.py      # LiteLLM cloud routing proxy
│   │       ├── models.py       # Model scanner and Hugging Face integration
│   │       ├── offload.py      # GPU layer calculation logic
│   │       └── routes/         # API route handlers
│   │       │   ├── __init__.py # Route aggregation
│   │       │   ├── chat.py     # Chat completion endpoints
│   │       │   ├── conversations.py # Chat history CRUD
│   │       │   ├── status.py   # Health and status endpoints
│   │       │   ├── control.py  # Service start/stop endpoints
│   │       │   └── models.py   # Model management endpoints
│   └── tests/                  # Backend tests (structure only)
│       └── __init__.py
├── scripts/                    # Installation and development scripts
│   ├── install.sh              # Unix/macOS installer
│   ├── install.ps1             # Windows installer
│   ├── dev.sh                  # Unix/macOS development script
│   ├── dev.ps1                 # Windows development script
│   ├── build.sh                # Unix/macOS build script
│   └── build.ps1               # Windows build script
└── README.md                   # Project documentation
```

## Directory Purposes

**[app/]:**
- Purpose: Contains the frontend application built with Svelte and wrapped with Tauri for desktop deployment
- Contains: Svelte components, stores, styles, and Tauri configuration
- Key files: `src/App.svelte` (root component), `src/main.ts` (entry point), `src-tauri/src/main.rs` (Tauri backend)

**[app/src/features/]:**
- Purpose: Organizes UI code by feature following feature-sliced design pattern
- Contains: Chat, models, and services features each with components and stores
- Key files: 
  - `features/chat/ChatPanel.svelte` (main chat interface)
  - `features/chat/ChatSidebar.svelte` (conversation history)
  - `features/models/ModelSelector.svelte` (model browsing)
  - `features/services/ServiceControls.svelte` (service management)

**[app/src/shared/]:**
- Purpose: Contains code shared across features
- Contains: TypeScript types, API client, theme management, utilities
- Key files: 
  - `shared/types.ts` (TypeScript interfaces for API)
  - `shared/api.ts` (HTTP client with streaming support)
  - `shared/theme.ts` (light/dark theme management)

**[app/src-tauri/]:**
- Purpose: Tauri-specific code for desktop application packaging
- Contains: Rust backend, Tauri configuration, icons, capabilities
- Key files:
  - `src-tauri/src/main.rs` (application entry point)
  - `src-tauri/tauri.conf.json` (window and build configuration)
  - `src-tauri/capabilities/main.json` (security permissions)

**[server/]:**
- Purpose: Contains the Python backend service that provides API endpoints and manages AI services
- Contains: FastAPI application, service integrations, data layers
- Key files:
  - `src/llmlaunchpad/main.py` (FastAPI app creation and middleware)
  - `src/llmlaunchpad/routes/` (API endpoint handlers)
  - `src/llmlaunchpad/llama.py` (llama.cpp process management)
  - `src/llmlaunchpad/models.py` (model discovery and Hugging Face integration)
  - `src/llmlaunchpad/database.py` (SQLite + FTS5 for chat history)

**[server/src/llmlaunchpad/routes/]:**
- Purpose: Organizes API endpoints by concern
- Contains: Route modules for different functional areas
- Key files:
  - `chat.py` (POST /chat for completions, SSE streaming)
  - `conversations.py` (CRUD for chat history, search, export)
  - `models.py` (model listing, scanning, downloading)
  - `control.py` (service start/stop/restart, configuration)
  - `status.py` (health checks, hardware info, service status)

**[scripts/]:**
- Purpose: Provides platform-specific installation and development utilities
- Contains: Shell and PowerShell scripts for setup, development, and building
- Key files:
  - `install.sh`/`install.ps1` (dependency installation with optional components)
  - `dev.sh`/`dev.ps1` (start development servers)
  - `build.sh`/`build.ps1` (create production builds)

## Key File Locations

**Entry Points:**
- `app/src/main.ts`: Frontend application entry point (Svelte)
- `app/src-tauri/src/main.rs`: Tauri desktop application entry point (Rust)
- `server/src/llmlaunchpad/main.py`: Backend API server entry point (Python/FastAPI)

**Configuration:**
- `server/src/llmlaunchpad/config.py`: Configuration loading, validation, and path resolution
- `tauri.conf.json`: Tauri window settings, bundling, and security configuration
- `app/src/shared/theme.ts`: Theme persistence and system preference handling

**Core Logic:**
- `server/src/llmlaunchpad/llama.py`: llama.cpp binary management (start/stop/monitor)
- `server/src/llmlaunchpad/models.py`: Model discovery from multiple sources (local, HF, etc.)
- `server/src/llmlaunchpad/offload.py`: GPU layer calculation based on VRAM and model size
- `server/src/llmlaunchpad/database.py`: SQLite database initialization and FTS5 search setup
- `app/src/shared/api.ts`: HTTP client with Server-Sent Events streaming support

**Testing:**
- `server/tests/`: Unit and integration tests for backend (structure established)
- Frontend testing: Co-located with components (would use .test.ts files)

## Naming Conventions

**Files:**
- kebab-case: Used for Svelte component files (e.g., `ChatPanel.svelte`)
- snake_case: Used for Python files (e.g., `hardware.py`, `models.py`)
- camelCase: Used for TypeScript/JavaScript files (e.g., `api.ts`, `main.ts`)
- PascalCase: Used for Svelte component class names and TypeScript interfaces (e.g., `LocalModel`, `ChatPanel`)

**Directories:**
- kebab-case: Feature directories (e.g., `features/chat`, `features/models`)
- snake_case: Python package directories (e.g., `src/llmlaunchpad`)
- camelCase: Not used for directories in this codebase

## Where to Add New Code

**New Feature:**
- Primary code: `app/src/features/[feature-name]/`
- Components: `app/src/features/[feature-name]/[ComponentName].svelte`
- Store: `app/src/features/[feature-name]/[feature-name].ts`
- Tests: Co-located with `.test.ts` files or in `tests/` directory

**New Backend Service:**
- Implementation: `server/src/llmlaunchpad/[service_name].py`
- API routes: `server/src/llmlaunchpad/routes/[service_name].py`
- Configuration: Add to `server/src/llmlaunchpad/config.py` if needed
- Tests: `server/tests/test_[service_name].py`

**New Utility/Helper:**
- Shared frontend: `app/src/shared/[utility_name].ts`
- Shared backend: `server/src/llmlaunchpad/utils/[utility_name].py` (would need to create utils directory)

**New Model Source:**
- Backend: Add scanning logic to `server/src/llmlaunchpad/models.py`
- Frontend: May need updates to `app/src/shared/types.ts` for new metadata fields
- API: Potentially extend `server/src/llmlaunchpad/routes/models.py` for new endpoints

## Special Directories

**[app/src-tauri/icons/]:**
- Purpose: Contains application icon assets for all supported platforms
- Generated: Yes (generated during build process)
- Committed: Yes (SVG source committed, PNG outputs generated)

**[server/.venv/]:**
- Purpose: Python virtual environment for dependency isolation
- Generated: Yes (created by installation scripts)
- Committed: No (listed in .gitignore)

**[app/node_modules/]:**
- Purpose: Node.js dependencies for frontend tooling
- Generated: Yes (created by npm install)
- Committed: No (listed in .gitignore)

**[app/dist/]:**
- Purpose: Built frontend assets for production
- Generated: Yes (created by vite build)
- Committed: No (listed in .gitignore, used by Tauri build)

**[app/src-tauri/target/]:**
- Purpose: Rust/Tauri build output and dependencies
- Generated: Yes (created by cargo build)
- Committed: No (listed in .gitignore)

---

*Structure analysis: 2026-03-28*