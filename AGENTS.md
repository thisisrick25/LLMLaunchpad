# LLMLaunchpad - Project Specification

## PROJECT GOAL

Build a lightweight local AI platform that works on Windows, Mac, and Linux.

### Core Features
- Tauri desktop app + browser-accessible web UI (same codebase)
- Python backend that orchestrates services
- llama.cpp as the local inference engine
- LiteLLM for optional cloud routing
- Automatic hardware detection
- Dynamic GPU/CPU offloading controls
- Chat interface with persistent history
- Real-time logs and service status
- Model management with Hugging Face integration

---

## HARD CONSTRAINTS

- Must stay lightweight
- No OpenWebUI
- No Docker dependency for core functionality
- No Electron
- Must run well on a Windows laptop with 8GB VRAM and 24GB RAM
- Must run well on Mac with similar specifications
- Must run well on Linux with similar specifications
- Prefer simple, modular, maintainable code
- Do not overbuild the UI
- Do not mix architecture and implementation in one step

---

## TECHNOLOGY STACK

| Layer | Technology |
|-------|------------|
| Frontend | Svelte + Vite + Tailwind CSS |
| State | Svelte stores (built-in) |
| Desktop | Tauri v2 |
| Backend | Python + FastAPI |
| Database | SQLite + FTS5 |
| Config | pyproject.toml |
| Inference | llama.cpp (llama-server) |
| Cloud | LiteLLM (optional) |

---

## FOLDER STRUCTURE

```
LLMLaunchpad/
├── README.md
├── AGENTS.md
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── .gitignore
│
├── app/                              # Svelte + Tauri (web + desktop)
│   ├── package.json
│   ├── vite.config.ts
│   ├── svelte.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   ├── index.html
│   ├── app-icon.svg
│   │
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.svelte
│   │   ├── app.css
│   │   │
│   │   ├── features/
│   │   │   ├── chat/
│   │   │   │   ├── ChatPanel.svelte
│   │   │   │   ├── ChatSidebar.svelte
│   │   │   │   └── chat.ts
│   │   │   ├── models/
│   │   │   │   ├── ModelSelector.svelte
│   │   │   │   └── models.ts
│   │   │   └── services/
│   │   │       ├── ServiceControls.svelte
│   │   │       ├── StatusBar.svelte
│   │   │       └── services.ts
│   │   │
│   │   └── shared/
│   │       ├── api.ts
│   │       └── types.ts
│   │
│   └── src-tauri/
│       ├── tauri.conf.json
│       ├── Cargo.toml
│       ├── build.rs
│       ├── capabilities/
│       │   └── main.json
│       ├── icons/
│       │   └── (generated icons)
│       └── src/
│           └── main.rs
│
├── server/
│   ├── pyproject.toml
│   ├── src/
│   │   └── llmlaunchpad/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── database.py
│   │       ├── hardware.py
│   │       ├── llama.py
│   │       ├── litellm.py
│   │       ├── models.py
│   │       ├── offload.py
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── chat.py
│   │           ├── conversations.py
│   │           ├── status.py
│   │           ├── control.py
│   │           └── models.py
│   └── tests/
│       └── __init__.py
│
└── scripts/
    ├── install.sh
    ├── install.ps1
    ├── dev.sh
    ├── dev.ps1
    ├── build.sh
    └── build.ps1
```

---

## DATA LOCATIONS

| Data | Windows | macOS/Linux |
|------|---------|-------------|
| Models | `C:\Users\<user>\.llmlaunchpad\models\` | `~/.llmlaunchpad/models/` |
| Config | `C:\Users\<user>\.llmlaunchpad\config.json` | `~/.llmlaunchpad/config.json` |
| Database | `C:\Users\<user>\.llmlaunchpad\data\chats.db` | `~/.llmlaunchpad/data/chats.db` |
| Logs | `C:\Users\<user>\.llmlaunchpad\logs\` | `~/.llmlaunchpad/logs/` |

---

## MODEL MANAGEMENT

### Download Sources
- Hugging Face Hub (browse, search, or paste URL)
- HF Token support for private models

### Local Model Scanning (GGUF only)
| Source | Path |
|--------|------|
| LLMLaunchpad | `~/.llmlaunchpad/models/` |
| LM Studio | `~/.cache/lm-studio/models/` |
| HF Cache | `~/.cache/huggingface/hub/` |
| GPT4All | `~/.local/share/nomic.ai/GPT4All/` |
| Jan.ai | `~/jan/models/` |
| Ollama | `~/.ollama/models/` (parse manifests, use blobs directly) |

### Recommended Models
- Llama 3.1 8B Instruct (Q4_K_M, Q5_K_M)
- Mistral 7B Instruct v0.3 (Q4_K_M, Q5_K_M)
- Phi-3 Mini 4K (Q4_K_M)
- Qwen2 7B Instruct (Q4_K_M)
- Gemma 2 9B Instruct (Q4_K_M)

---

## CHAT HISTORY

| Feature | Implementation |
|---------|----------------|
| Storage | SQLite at `~/.llmlaunchpad/data/chats.db` |
| Search | Full-text search (SQLite FTS5) |
| Export | JSON + Markdown |
| Title | Auto-generate from first message + manual edit |
| Retention | Forever (no auto-delete) |

---

## PERFORMANCE MODES

| Mode | Behavior |
|------|----------|
| Auto | Detect GPU VRAM, calculate optimal --n-gpu-layers |
| GPU-Heavy | Maximize GPU layers (may swap to RAM) |
| CPU-Only | Set --n-gpu-layers 0, pure CPU inference |
| Cloud | Use LiteLLM to route to cloud providers |

---

## INSTALLATION OPTIONS

### Install Scripts

| Script | Platform | Description |
|--------|----------|-------------|
| `scripts/install.sh` | Unix/macOS | Interactive installer with optional components |
| `scripts/install.ps1` | Windows | Interactive installer with optional components |
| `scripts/dev.sh` | Unix/macOS | Start dev servers (--tauri for desktop) |
| `scripts/dev.ps1` | Windows | Start dev servers (-Tauri for desktop) |
| `scripts/build.sh` | Unix/macOS | Build for production (--tauri, --all) |
| `scripts/build.ps1` | Windows | Build for production (-Tauri, -All) |

### Install Script Options

| Flag | Description |
|------|-------------|
| `--all` / `-All` | Install all optional components |
| `--minimal` / `-Minimal` | Install only core (no optional) |
| `--no-prompt` / `-NoPrompt` | Non-interactive mode |
| `--skip-tauri` / `-SkipTauri` | Skip Rust/Tauri check |

### Optional Components

Components are detected if already installed and skipped automatically.

| Component | Description | Pip Extra |
|-----------|-------------|-----------|
| llama.cpp | Local inference engine (binary download) | N/A |
| Hugging Face Hub | Model downloads from HF | `hf` |
| LiteLLM | Cloud model routing (OpenAI, Anthropic) | `cloud` |
| GPU Support | NVIDIA GPU detection (GPUtil) | `gpu` |

### Pip Install Examples

```bash
# Core only (minimal)
pip install -e .

# With Hugging Face
pip install -e ".[hf]"

# With cloud routing
pip install -e ".[cloud]"

# All optional
pip install -e ".[all]"
```

### Packaged Installers (Future)

| Method | Platform |
|--------|----------|
| .exe installer | Windows |
| .dmg / Homebrew | macOS |
| .AppImage / .deb | Linux |

---

## WORK STYLE

Use a phased approach:
1. Plan the architecture (COMPLETE)
2. Build the skeleton
3. Implement backend
4. Implement chat and routing
5. Implement frontend
6. Integrate frontend and backend
7. Package for Tauri
8. Prepare packaging and run instructions

Do not try to implement everything at once.

---

## DELIVERABLE RULES

- Make changes file by file
- Show the file tree before large changes
- Keep each phase small and verifiable
- Use clear filenames and module boundaries
- Include error handling
- Avoid placeholders unless absolutely necessary
- Prefer working code over speculative code

---

## PHASE STATUS

### Phase 1: Architecture Planning ✅ COMPLETE
- Folder structure defined
- API endpoints defined
- Technology stack chosen
- Data locations defined
- Feature specifications complete

### Phase 2: Project Skeleton ✅ COMPLETE
- Root package.json with concurrently for dev workflow
- Backend FastAPI project with pyproject.toml
- Frontend Svelte + Vite + Tailwind project
- /health and /status endpoints working
- Vite proxy configured for API routing

### Phase 3: Backend Implementation ✅ COMPLETE
- `hardware.py` - CPU/GPU/RAM detection (NVIDIA, AMD, Apple Silicon)
- `llama.py` - llama.cpp process management (start/stop/monitor)
- `offload.py` - GPU layer calculation based on VRAM/model size
- `litellm.py` - LiteLLM cloud routing proxy
- `models.py` - Model scanner (LLMLaunchpad, LM Studio, HF Cache, GPT4All, Jan, Ollama)
- `database.py` - SQLite + FTS5 for chat history
- `config.py` - Configuration persistence
- `routes/status.py` - Health and status endpoints
- `routes/control.py` - Service start/stop endpoints
- `routes/models.py` - Model list/scan/download endpoints
- `routes/chat.py` - Chat with SSE streaming
- `routes/conversations.py` - Chat history CRUD + search + export

### Phase 4: Frontend Implementation ✅ COMPLETE
- `shared/types.ts` - TypeScript types for API
- `shared/api.ts` - Full API client with streaming support
- `features/chat/chat.ts` - Chat Svelte store
- `features/chat/ChatPanel.svelte` - Chat UI with streaming display
- `features/chat/ChatSidebar.svelte` - Conversation history with search/export
- `features/services/services.ts` - Services Svelte store
- `features/services/ServiceControls.svelte` - Start/stop server controls
- `features/services/StatusBar.svelte` - Status bar with log viewer
- `features/models/models.ts` - Models Svelte store
- `features/models/ModelSelector.svelte` - Model browser with HF search/download
- `App.svelte` - Full integrated layout with collapsible panels

### Phase 5: Tauri Integration ✅ COMPLETE
- `src-tauri/Cargo.toml` - Rust project with Tauri v2 dependencies
- `src-tauri/tauri.conf.json` - Window config, bundling, permissions
- `src-tauri/capabilities/main.json` - Tauri v2 capability permissions
- `src-tauri/src/main.rs` - Tauri application entry point
- `src-tauri/icons/*` - App icons for all platforms
- `vite.config.ts` - Updated for Tauri compatibility
- Build produces: .exe, .msi, NSIS installer (Windows)
- Scripts: `npm run dev:tauri`, `npm run build:tauri`

### Phase 6: Packaging ✅ COMPLETE
- `scripts/install.sh` - Unix/macOS installer with prerequisite checks
- `scripts/install.ps1` - Windows installer with prerequisite checks
- `scripts/dev.sh` - Unix/macOS dev script with --tauri option
- `scripts/dev.ps1` - Windows dev script with -Tauri option
- `scripts/build.sh` - Unix/macOS build script with --tauri, --all options
- `scripts/build.ps1` - Windows build script with -Tauri, -All options
- Data directory creation (~/.llmlaunchpad/models, data, logs)
- README.md with installation and usage documentation

---

## SUCCESS CRITERIA

A user should be able to:
- Open the app in browser or desktop
- Pick a performance mode
- Select a GGUF model (local or download from HF)
- Start the stack with one click
- Have llama.cpp launch with the right offloading settings
- Optionally route through cloud models
- Chat through the UI with streaming
- Search chat history
- Export conversations
- View logs and service health in real time

---

## IMPORTANT OUTPUT STYLE

When coding:
- Keep the response focused on the current phase only
- Do not jump ahead
- Do not produce huge monolithic dumps
- Prefer one file at a time
- If something is ambiguous, make the best reasonable assumption and state it briefly
