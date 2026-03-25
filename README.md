# LLMLaunchpad

A lightweight local AI platform that works on Windows, Mac, and Linux. Run open-source LLMs locally with automatic hardware detection and optimal GPU/CPU offloading.

## Features

- **Desktop & Web**: Tauri desktop app + browser-accessible web UI (same codebase)
- **Local Inference**: llama.cpp as the inference engine with automatic GPU layer optimization
- **Cloud Routing**: Optional LiteLLM integration for cloud model access
- **Hardware Detection**: Automatic CPU/GPU/RAM detection (NVIDIA, AMD, Apple Silicon)
- **Model Management**: Browse, search, and download models from Hugging Face
- **Multi-Source Scanning**: Finds GGUF models from LM Studio, HF Cache, GPT4All, Jan.ai, Ollama
- **Chat History**: SQLite-backed persistent history with full-text search
- **Export**: Export conversations to JSON or Markdown

## Quick Start

### Prerequisites

| Requirement | Version |
|-------------|---------|
| [Node.js](https://nodejs.org/) | 18+ |
| [Python](https://www.python.org/) | 3.10+ |
| [llama.cpp](https://github.com/ggerganov/llama.cpp) | Latest (llama-server binary) |
| [Rust](https://www.rust-lang.org/tools/install) | 1.70+ (desktop app only) |

**Platform-specific for desktop app:**
- **Windows**: Visual Studio Build Tools with C++ workload, WebView2 (pre-installed on Win 10/11)
- **macOS**: Xcode Command Line Tools (`xcode-select --install`)
- **Linux**: WebKit2GTK 4.1+ ([Tauri prerequisites](https://v2.tauri.app/start/prerequisites/))

### Installation

```bash
git clone https://github.com/your-username/LLMLaunchpad.git
cd LLMLaunchpad

# Frontend
npm run install:app

# Backend
cd server
python -m venv .venv

# Activate venv (pick one):
.venv\Scripts\Activate.ps1      # Windows PowerShell
.venv\Scripts\activate.bat      # Windows cmd
source .venv/bin/activate       # macOS/Linux

# Install (with venv activated)
pip install -e ".[all]"         # All features
# Or minimal: pip install -e .
```

### Run

```bash
# Activate venv first, then from project root:
npm run dev          # Web UI at http://localhost:5173
npm run dev:tauri    # Desktop app
```

## Usage

| Command | Description |
|---------|-------------|
| `npm run dev` | Web UI + backend |
| `npm run dev:tauri` | Desktop app + backend |
| `npm run build` | Build frontend |
| `npm run build:tauri` | Build desktop installers |

## Configuration

### llama.cpp

Download [llama.cpp](https://github.com/ggerganov/llama.cpp) and ensure `llama-server` is in your PATH or configure the path in app settings.

### Model Locations

LLMLaunchpad scans for GGUF models in:

| Source | Path |
|--------|------|
| LLMLaunchpad | `~/.llmlaunchpad/models/` |
| LM Studio | `~/.cache/lm-studio/models/` |
| HuggingFace | `~/.cache/huggingface/hub/` |
| GPT4All | `~/.local/share/nomic.ai/GPT4All/` |
| Jan.ai | `~/jan/models/` |
| Ollama | `~/.ollama/models/` |

### Performance Modes

| Mode | Description |
|------|-------------|
| Auto | Optimal GPU layers based on VRAM |
| GPU-Heavy | Maximize GPU (may swap) |
| CPU-Only | No GPU acceleration |
| Cloud | Route via LiteLLM |

### Data Storage

| Data | Location |
|------|----------|
| Models | `~/.llmlaunchpad/models/` |
| Config | `~/.llmlaunchpad/config.json` |
| Chat History | `~/.llmlaunchpad/data/chats.db` |
| Logs | `~/.llmlaunchpad/logs/` |

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status |
| `/models` | GET | List models |
| `/models/scan` | POST | Rescan models |
| `/models/search` | GET | Search HuggingFace |
| `/models/download` | POST | Download from HF |
| `/control/start` | POST | Start llama.cpp |
| `/control/stop` | POST | Stop llama.cpp |
| `/chat` | POST | Chat (SSE streaming) |
| `/conversations` | GET | List conversations |
| `/conversations/{id}` | GET/DELETE | Get/delete conversation |
| `/conversations/{id}/export` | GET | Export conversation |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Svelte + Vite + Tailwind CSS |
| Desktop | Tauri v2 |
| Backend | Python + FastAPI |
| Database | SQLite + FTS5 |
| Inference | llama.cpp |
| Cloud | LiteLLM (optional) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and PR guidelines.

## License

MIT

## Acknowledgements

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Local LLM inference
- [Tauri](https://tauri.app/) - Desktop framework
- [Svelte](https://svelte.dev/) - Frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [LiteLLM](https://github.com/BerriAI/litellm) - Cloud model routing
