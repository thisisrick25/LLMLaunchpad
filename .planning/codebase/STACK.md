# Technology Stack

**Analysis Date:** 2026-03-28

## Languages

**Primary:**
- TypeScript 5.4.5 - Frontend application (app/src/)
- Python >=3.10 - Backend services (server/src/)

**Secondary:**
- Rust - Tauri desktop wrapper (app/src-tauri/src/)

## Runtime

**Environment:**
- Node.js (version not specified in lockfile, but compatible with Vite 5.2.11)
- Python 3.10+ runtime

**Package Manager:**
- npm/node: package-lock.json present (version 3)
- Python: pip/pyproject.toml with lockfile implied by poetry/uv or similar
- Rust: Cargo.lock (implied by Tauri usage)

## Frameworks

**Core:**
- Svelte 4.2.17 - Frontend UI framework
- Vite 5.2.11 - Frontend build tool and dev server
- Tauri 2.0.0 - Desktop application wrapper
- FastAPI 0.109.0 - Backend web framework
- Uvicorn 0.27.0 - ASGI server for FastAPI

**Testing:**
- Vitest (implied by Vite ecosystem) - Frontend testing
- Pytest 7.0.0+ - Backend testing
- Playwright/Test (not explicitly listed but common with Svelte) - E2E testing (not detected in config)

**Build/Dev:**
- TailwindCSS 3.4.3 - Utility-first CSS framework
- PostCSS 8.4.38 - CSS processing
- Autoprefixer 10.4.19 - CSS vendor prefixing
- TypeScript 5.4.5 - Type checking
- Svelte-check 3.7.1 - Svelte TypeScript validation
- Concurrently 9.2.1 - Process management for dev scripts

## Key Dependencies

**Critical:**
- @tauri-apps/api 2.0.0 - Tauri frontend API bridge
- @tauri-apps/plugin-shell 2.3.5 - Shell integration for Tauri
- FastAPI 0.109.0 - High-performance Python web framework
- Uvicorn[standard]>=0.27.0 - ASGI server with standard dependencies
- Pydantic>=2.0.0 - Data validation and settings management
- aiosqlite>=0.19.0 - Async SQLite database driver
- httpx>=0.25.0 - Async HTTP client
- sse-starlette>=1.8.0 - Server-Sent Events support
- psutil>=5.9.0 - System monitoring and hardware detection

**Infrastructure:**
- llama.cpp - Local LLM inference engine (binary download, not npm/pip package)
- LiteLLM>=1.30.0 - Cloud model routing (optional)
- Hugging Face Hub>=0.20.0 - Model downloads (optional)
- GPUtil>=1.4.0 - NVIDIA GPU detection (optional)

## Configuration

**Environment:**
- Environment variables for configuration (see server/src/llmlaunchpad/config.py)
- Key configs: MODELS_DIR, DATA_DIR, LOG_DIR, HF_TOKEN, etc.
- Configuration persistence via JSON file in user directory

**Build:**
- Vite configuration: vite.config.ts
- Tauri configuration: tauri.conf.json
- Rust build: Cargo.toml + build.rs
- Python packaging: pyproject.toml
- PostCSS/Tailwind: tailwind.config.js + postcss.config.js

## Platform Requirements

**Development:**
- Node.js (LTS recommended)
- Python 3.10+
- Rust toolchain (for Tauri)
- Git
- C/C++ build tools (for native dependencies)

**Production:**
- Windows 10+/11, macOS 12+, Linux (various distributions)
- Minimum 8GB RAM recommended, 16GB+ for larger models
- GPU acceleration supported on NVIDIA (CUDA), with CPU fallback

---

*Stack analysis: 2026-03-28*