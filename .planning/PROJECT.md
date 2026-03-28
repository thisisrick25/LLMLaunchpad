# LLMLaunchpad - Project Context

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

### Hard Constraints
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

### Technology Stack
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

### Data Locations
| Data | Windows | macOS/Linux |
|------|---------|-------------|
| Models | `C:\Users\<user>\.llmlaunchpad\models\` | `~/.llmlaunchpad/models/` |
| Config | `C:\Users\<user>\.llmlaunchpad\config.json` | `~/.llmlaunchpad/config.json` |
| Database | `C:\Users\<user>\.llmlaunchpad\data\chats.db` | `~/.llmlaunchpad/data/chats.db` |
| Logs | `C:\Users\<user>\.llmlaunchpad\logs\` | `~/.llmlaunchpad/logs/` |

### Model Management
- Download Sources: Hugging Face Hub (browse, search, or paste URL), HF Token support for private models
- Local Model Scanning (GGUF only): LLMLaunchpad, LM Studio, HF Cache, GPT4All, Jan.ai, Ollama
- Recommended Models: Llama 3.1 8B Instruct, Mistral 7B Instruct v0.3, Phi-3 Mini 4K, Qwen2 7B Instruct, Gemma 2 9B Instruct (various quantizations)

### Chat History
- Storage: SQLite at `~/.llmlaunchpad/data/chats.db`
- Search: Full-text search (SQLite FTS5)
- Export: JSON + Markdown
- Title: Auto-generate from first message + manual edit
- Retention: Forever (no auto-delete)

### Performance Modes
| Mode | Behavior |
|------|----------|
| Auto | Detect GPU VRAM, calculate optimal --n-gpu-layers |
| GPU-Heavy | Maximize GPU layers (may swap to RAM) |
| CPU-Only | Set --n-gpu-layers 0, pure CPU inference |
| Cloud | Use LiteLLM to route to cloud providers |

### Installation Options
- Install Scripts: `scripts/install.sh` (Unix/macOS), `scripts/install.ps1` (Windows)
- Dev Scripts: `scripts/dev.sh` (Unix/macOS), `scripts/dev.ps1` (Windows)
- Build Scripts: `scripts/build.sh` (Unix/macOS), `scripts/build.ps1` (Windows)
- Optional Components: llama.cpp, Hugging Face Hub, LiteLLM, GPU Support

### Success Criteria
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