# External Integrations

**Analysis Date:** 2026-03-28

## APIs & External Services

**AI Model Providers:**
- **Local Inference:** llama.cpp (binary executable)
  - Used for: Running GGUF format models locally
  - Integration: Process spawning and management via `llama.py`
  - Configuration: Command-line arguments (--n-gpu-layers, --ctx-size, etc.)
- **Cloud Providers (via LiteLLM):**
  - OpenAI - GPT series (gpt-4o, gpt-4o-mini, etc.)
  - Anthropic - Claude series (claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022)
  - Google - Gemini series (gemini-1.5-pro, gemini-1.5-flash)
  - Azure - Azure OpenAI Service
  - Groq - Llama models on Groq hardware
  - Together - Various open-source models
  - Mistral - Mistral series models
  - SDK/Client: `litellm` Python package (optional)
  - Auth: API keys stored in configuration (`litellm_api_keys` in config.json) and applied as environment variables

**Model Repositories:**
- **Hugging Face Hub:**
  - Used for: Downloading GGUF and other model formats
  - SDK/Client: `huggingface-hub` Python package (optional)
  - Auth: `HF_TOKEN` environment variable or config for private models
  - Endpoints: https://huggingface.co/api

**Local Model Sources (Scanned, Not Integrated):**
- LM Studio models: `~/.cache/lm-studio/models/`
- Hugging Face cache: `~/.cache/huggingface/hub/`
- GPT4All models: `~/.local/share/nomic.ai/GPT4All/`
- Jan.ai models: `~/jan/models/`
- Ollama models: `~/.ollama/models/` (manifests parsed, blobs used directly)

## Data Storage

**Databases:**
- **SQLite with FTS5:**
  - Used for: Chat history storage and full-text search
  - Connection: File path configured in `config.py` (`DATA_DIR/chats.db`)
  - Client: Direct SQL via `aiosqlite` (async) and `sqlite3` (sync)
  - Host: Local filesystem only

**File Storage:**
- **Local filesystem only:**
  - Models: Stored in `MODELS_DIR` (default: `~/.llmlaunchpad/models/`)
  - Configuration: `config.json` in `~/.llmlaunchpad/`
  - Logs: Log files in `LOG_DIR` (default: `~/.llmlaunchpad/logs/`)

**Caching:**
- **HTTP Caching:** None explicit (relies on browser/cache control)
- **Model Caching:** Downloaded models stored locally in models directory
- **HF Hub Cache:** Uses `huggingface-hub` cache if enabled (~/.cache/huggingface/hub/)

## Authentication & Identity

**Auth Provider:**
- **Custom/None for local use:** No authentication required for local operation
- **API Key Management:** For cloud providers only
  - Storage: Encrypted? Currently stored in plain text in config.json
  - Providers: OpenAI, Anthropic, Google, Azure, Groq, Together, Mistral
  - Application: Set as environment variables for LiteLLM

## Monitoring & Observability

**Error Tracking:**
- **None integrated:** Errors logged to console and log files

**Logs:**
- **Approach:** Python logging module + file output
- **Configuration:** Log level and file path configurable via `config.py`
- **Destinations:** Console and rotating file handler in `LOG_DIR`
- **Frontend:** Log viewing via StatusBar component (reads from log files)

## CI/CD & Deployment

**Hosting:**
- **Self-hosted only:** Designed for local execution
- **Distribution:** Packaged executables via Tauri (.exe, .msi, .dmg, .AppImage, etc.)

**CI Pipeline:**
- **None configured:** No CI/CD files present (.github/, .gitlab-ci.yml, etc.)
- **Local development:** Scripts in `scripts/` for dev/build

## Environment Configuration

**Required env vars:**
- None required for core operation
- Optional:
  - `HF_TOKEN`: For accessing private Hugging Face models
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.: For cloud provider access
  - `LLM_LAUNCHPAD_*`: Override config values (see config.py)

**Secrets location:**
- `~/.llmlaunchpad/config.json` - Stores API keys in plain text (consider encryption in future)
- Environment variables (runtime only)

## Webhooks & Callbacks

**Incoming:**
- **None:** No webhook endpoints exposed

**Outgoing:**
- **None:** No outgoing webhooks configured
- **HTTP requests:** 
  - To Hugging Face Hub for model metadata/download
  - To cloud provider APIs via LiteLLM (when enabled)

---

*Integration audit: 2026-03-28*