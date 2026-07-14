# LLMLaunchpad - Technical Architecture

> **Implementation Status:** Phases 1-5 Complete (Architecture, Skeleton, Backend, Frontend, Tauri)

## API ENDPOINTS

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Basic health check `{"status": "ok"}` |
| `GET` | `/status` | Full status (services, hardware, config, active model) |
| `GET` | `/hardware` | Detected GPU/CPU/RAM info |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/config` | Current configuration |
| `POST` | `/config` | Update configuration |

### Model Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/models` | List all local GGUF (ours + scanned sources) |
| `GET` | `/models/sources` | List available model sources with status |
| `POST` | `/models/scan` | Force rescan all sources |
| `GET` | `/models/recommended` | Curated download list from HF |
| `POST` | `/models/hf/search` | Search HF for GGUF models |
| `POST` | `/models/hf/parse` | Parse HF URL/ID |
| `POST` | `/models/hf/files` | List available GGUF files for a repo |
| `POST` | `/models/download` | Start downloading a model from HF |
| `GET` | `/models/downloads` | Check download progress |
| `GET` | `/models/{model_name}` | Get details for a specific model |

### Service Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/control/start` | Start llama.cpp (+ optional LiteLLM) |
| `POST` | `/control/stop` | Stop running services |
| `POST` | `/control/restart` | Restart services |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/completions` | Send message, returns SSE stream |
| `POST` | `/chat/abort` | Cancel current generation |

### Conversations (Chat History)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/conversations` | List all conversations (paginated) |
| `POST` | `/conversations` | Create new conversation |
| `GET` | `/conversations/{id}` | Get conversation with messages |
| `DELETE` | `/conversations/{id}` | Delete conversation |
| `PATCH` | `/conversations/{id}` | Update title |
| `GET` | `/conversations/search?q=...` | Full-text search messages |
| `GET` | `/conversations/{id}/export/json` | Export as JSON |
| `GET` | `/conversations/{id}/export/markdown` | Export as Markdown |

### Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/logs` | Get recent log lines |
| `WS` | `/logs/stream` | WebSocket for real-time logs |

---

## DATABASE SCHEMA

```sql
-- Conversations table
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,              -- UUID
    title TEXT,                       -- Auto-generated or user-set
    model TEXT,                       -- Model used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id TEXT PRIMARY KEY,              -- UUID
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,               -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Full-text search index for messages
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=rowid
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
END;

CREATE TRIGGER messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.rowid, old.content);
END;

CREATE TRIGGER messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.rowid, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
END;

-- Indexes
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);
```

---

## CONFIGURATION SCHEMA

```python
@dataclass
class Config:
    # Paths (platform-specific defaults)
    models_dir: str = "~/.llmlaunchpad/models"
    data_dir: str = "~/.llmlaunchpad/data"
    logs_dir: str = "~/.llmlaunchpad/logs"
    llama_binary: str = ""                    # Auto-detected or user-set
    
    # Hugging Face
    hf_token: Optional[str] = None
    
    # Performance mode
    mode: str = "auto"                        # auto | gpu-heavy | cpu-only | cloud
    
    # Manual overrides
    gpu_layers: Optional[int] = None          # Override auto-calculated layers
    context_size: int = 4096
    
    # LiteLLM (cloud routing)
    litellm_enabled: bool = False
    litellm_api_keys: dict = {}               # {"openai": "sk-...", "anthropic": "..."}
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
```

---

## MODEL SCANNER PATHS

### Windows

| Source | Path |
|--------|------|
| LLMLaunchpad | `C:\Users\<user>\.llmlaunchpad\models\` |
| LM Studio | `C:\Users\<user>\.cache\lm-studio\models\` |
| HF Cache | `C:\Users\<user>\.cache\huggingface\hub\` |
| GPT4All | `%LOCALAPPDATA%\nomic.ai\GPT4All\` |
| Jan.ai | `C:\Users\<user>\jan\models\` |
| Ollama | `C:\Users\<user>\.ollama\models\` |

### macOS / Linux

| Source | Path |
|--------|------|
| LLMLaunchpad | `~/.llmlaunchpad/models/` |
| LM Studio | `~/.cache/lm-studio/models/` |
| HF Cache | `~/.cache/huggingface/hub/` |
| GPT4All | `~/.local/share/nomic.ai/GPT4All/` |
| Jan.ai | `~/jan/models/` |
| Ollama | `~/.ollama/models/` |

### Ollama Special Handling

Ollama stores models as blobs, not raw GGUF files. We parse manifests to find the blob paths:

```
~/.ollama/models/
├── manifests/
│   └── registry.ollama.ai/
│       └── library/
│           └── llama3/
│               └── latest           # JSON manifest
└── blobs/
    └── sha256-abc123...             # Actual GGUF data (use directly)
```

---

## SERVICE LIFECYCLE

```
[App Start]
    │
    ▼
[Backend boots]
    ├── Detect hardware (GPU/CPU/RAM)
    ├── Load config
    ├── Initialize SQLite database
    ├── Scan models/ for local GGUFs
    └── Start FastAPI server
    │
    ▼
[Frontend connects]
    └── GET /status → Receives hardware, config, models, service state
    │
    ▼
[User browses models] (optional)
    ├── GET /models → See all local models
    ├── GET /models/recommended → Show curated list
    ├── POST /models/hf/search → Search HF
    ├── POST /models/hf/parse → Parse HF URL, list files
    └── POST /models/download → Download with progress
    │
    ▼
[User selects model + mode]
    │
    ▼
[User clicks Start]
    │
    ▼
[POST /control/start]
    ├── Calculate GPU layers based on mode + hardware + model size
    ├── Spawn: llama-server --model X.gguf --n-gpu-layers N --ctx-size 4096
    ├── (Optional) Spawn LiteLLM proxy
    └── Return status
    │
    ▼
[Service running]
    ├── POST /chat/completions → Stream tokens via SSE
    ├── Messages saved to SQLite
    └── WS /logs/stream → Real-time log tailing
    │
    ▼
[User clicks Stop]
    │
    ▼
[POST /control/stop]
    └── Graceful shutdown of llama.cpp + LiteLLM
```

---

## HARDWARE DETECTION

| Platform | GPU Detection | Method |
|----------|---------------|--------|
| Windows/Linux (NVIDIA) | CUDA GPUs | `GPUtil` or `pynvml` |
| Windows/Linux (AMD) | ROCm GPUs | Parse `rocm-smi` output |
| macOS (Apple Silicon) | Metal | `system_profiler SPDisplaysDataType` |
| macOS (Intel) | Discrete GPU | `system_profiler` |
| All | RAM/CPU | `psutil` |

---

## GPU LAYER CALCULATION

```python
def calculate_gpu_layers(model_size_bytes: int, vram_bytes: int, mode: str) -> int:
    """Calculate optimal --n-gpu-layers for llama.cpp"""
    
    if mode == "cpu-only":
        return 0
    
    if mode == "cloud":
        return 0  # Not using local inference
    
    # Estimate: ~60% of model size needed in VRAM for inference
    estimated_vram_needed = model_size_bytes * 0.6
    
    # Reserve 1GB for system
    available_vram = vram_bytes - (1 * 1024 * 1024 * 1024)
    
    if mode == "gpu-heavy":
        # Try to fit entire model, may use RAM
        return 999  # llama.cpp will use max possible
    
    # Auto mode: calculate safe layers
    if available_vram >= estimated_vram_needed:
        return 999  # Full GPU offload
    
    # Partial offload
    ratio = available_vram / estimated_vram_needed
    estimated_total_layers = 35  # Typical for 7B model
    return max(0, int(estimated_total_layers * ratio))
```

---

## FRONTEND COMPONENTS

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ Model: [▼ list] │  │ Mode: [▼ auto]  │  │ [⚙ Settings]   │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                │
│  [▶ Start] [■ Stop] [↻ Restart]     Status: ● Running          │
│  GPU: RTX 3070 8GB | Layers: 33/35 | RAM: 12GB used            │
├───────────┬────────────────────────────────────────────────────┤
│           │                                                    │
│  SIDEBAR  │              CHAT PANEL                            │
│           │                                                    │
│ [+ New]   │  User: What is the capital of France?              │
│           │  Assistant: The capital of France is Paris.        │
│ 🔍 Search │                                                    │
│           │                                                    │
│ Today     │                                                    │
│  • Chat 1 │                                                    │
│  • Chat 2 │ ┌────────────────────────────────────────────────┐ │
│           │ │ Type a message...                    [Send ➤]  │ │
│ Yesterday │ └────────────────────────────────────────────────┘ │
│  • Chat 3 │                                                    │
├───────────┴────────────────────────────────────────────────────┤
│  ▼ Logs (collapsible)                                          │
│  [INFO] llama.cpp loaded model in 2.3s                         │
│  [INFO] GPU layers: 33, CPU layers: 2                          │
└────────────────────────────────────────────────────────────────┘
```

### Component Tree

```
App.svelte
├── features/
│   ├── chat/
│   │   ├── ChatPanel.svelte         # Main chat area with streaming
│   │   ├── ChatSidebar.svelte       # History list + search + export
│   │   └── chat.ts                  # Chat store
│   ├── models/
│   │   ├── ModelSelector.svelte     # Browse local + download from HF
│   │   └── models.ts                # Models store
│   └── services/
│       ├── ServiceControls.svelte   # Start/Stop + model/mode selection
│       ├── StatusBar.svelte         # Service state + hardware + logs
│       └── services.ts              # Services store
└── shared/
    ├── api.ts                       # API client with streaming
    └── types.ts                     # TypeScript types
```

---

## BACKEND MODULES

```
server/src/llmlaunchpad/
├── __init__.py
├── main.py              # FastAPI app, startup/shutdown
├── config.py            # Config loading, platform paths, defaults
├── database.py          # SQLite + FTS5 setup, query helpers
├── hardware.py          # GPU/CPU/RAM detection
├── llama.py             # llama.cpp process management
├── litellm.py           # LiteLLM proxy management
├── models.py            # Model scanner + HF downloader
├── offload.py           # GPU layer calculation
└── routes/
    ├── __init__.py      # Router aggregation
    ├── chat.py          # POST /chat/completions (SSE streaming)
    ├── conversations.py # CRUD + search + export
    ├── status.py        # GET /health, /status, /hardware
    ├── control.py       # POST /control/*
    └── models.py        # GET/POST /models/*
```

---

## DEPENDENCIES

### Backend (pyproject.toml)

```toml
[project]
name = "llmlaunchpad"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "huggingface-hub>=0.20.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "psutil>=5.9.0",
    "GPUtil>=1.4.0",
    "sse-starlette>=1.8.0",
    "aiosqlite>=0.19.0",
]
```

### Frontend (package.json)

```json
{
  "devDependencies": {
    "vite": "^5.0.0",
    "svelte": "^4.2.0",
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@tauri-apps/cli": "^2.0.0",
    "@tauri-apps/api": "^2.0.0"
  }
}
```

---

## EXPORT FORMATS

### JSON Export

```json
{
  "id": "abc-123",
  "title": "Capital of France",
  "model": "llama-3.1-8b-instruct.Q4_K_M",
  "created_at": "2025-03-20T10:30:00Z",
  "messages": [
    {"role": "user", "content": "What is the capital of France?", "created_at": "..."},
    {"role": "assistant", "content": "The capital of France is Paris.", "created_at": "..."}
  ]
}
```

### Markdown Export

```markdown
# Capital of France

**Model:** llama-3.1-8b-instruct.Q4_K_M  
**Date:** March 20, 2025

---

**User:**  
What is the capital of France?

**Assistant:**  
The capital of France is Paris.
```

---

## TAURI CONFIGURATION

### Build Configuration (tauri.conf.json)

```json
{
  "productName": "LLMLaunchpad",
  "version": "0.1.0",
  "identifier": "com.llmlaunchpad.desktop",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:5173",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [{
      "title": "LLMLaunchpad",
      "width": 1280,
      "height": 800,
      "minWidth": 800,
      "minHeight": 600
    }]
  }
}
```

### Capabilities (Tauri v2 Permissions)

```json
{
  "identifier": "main-capability",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-open"
  ]
}
```

### Build Outputs

| Platform | Output |
|----------|--------|
| Windows | `.exe` (standalone), `.msi` (installer), `.exe` (NSIS installer) |
| macOS | `.app` (bundle), `.dmg` (disk image) |
| Linux | `.AppImage`, `.deb` |

---

## DEVELOPMENT SCRIPTS

### Root package.json Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start web UI + backend (browser mode) |
| `npm run dev:tauri` | Start Tauri app + backend (desktop mode) |
| `npm run dev:app` | Start frontend only (port 5173) |
| `npm run dev:server` | Start backend only (port 8000) |
| `npm run build` | Build frontend for production |
| `npm run build:tauri` | Build desktop installers |
| `npm run install:all` | Install all dependencies |

### Vite Configuration

The Vite config includes:
- Proxy `/api/*` to backend on port 8000
- Tauri-specific settings (strict port, env prefix)
- Sourcemaps for debug builds
- Platform-specific build targets
