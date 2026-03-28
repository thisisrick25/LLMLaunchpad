# LLMLaunchpad - Scoped Requirements

## Core Features (Must Be Included)

### 1. Cross-Platform Desktop & Web Application
- Tauri v2 desktop application for Windows, macOS, and Linux
- Browser-accessible web UI sharing the same Svelte/Vite codebase
- Single codebase for both desktop and web interfaces

### 2. Python Backend Orchestration
- FastAPI-based backend service
- Service lifecycle management (start/stop/restart)
- API endpoints for all functionality
- Configuration persistence

### 3. Local Inference Engine
- llama.cpp (llama-server) as the primary inference engine
- Automatic binary download and management
- GGUF model format support only
- Process monitoring and control

### 4. Optional Cloud Routing
- LiteLLM integration for cloud provider routing
- Support for OpenAI, Anthropic, and other providers via LiteLLM
- Toggleable cloud/local inference modes

### 5. Automatic Hardware Detection
- Cross-platform GPU detection (NVIDIA CUDA, AMD ROCm, Apple Silicon Metal)
- CPU and RAM detection via psutil
- VRAM measurement for accurate GPU layer calculation
- Fallback mechanisms for undetectable hardware

### 6. Dynamic GPU/CPU Offloading Controls
- Four performance modes: Auto, GPU-Heavy, CPU-Only, Cloud
- Automatic GPU layer calculation based on VRAM and model size
- Manual override capability for advanced users
- Safe defaults to prevent OOM conditions

### 7. Chat Interface with Persistent History
- Streaming chat UI with real-time token display
- Conversation persistence using SQLite database
- Full-text search (FTS5) on chat history
- Conversation export (JSON and Markdown formats)
- Auto-generated conversation titles with manual edit capability
- Infinite retention (no auto-deletion)

### 8. Real-Time Logs and Service Status
- Live logging interface with WebSocket streaming
- Service health monitoring (llama.cpp, LiteLLM)
- Hardware utilization display (GPU VRAM, CPU, RAM usage)
- Active model and performance mode indicators

### 9. Model Management with Hugging Face Integration
- Local GGUF model scanning from multiple sources:
  - LLMLaunchpad models directory
  - LM Studio cache
  - Hugging Face cache
  - GPT4All directory
  - Jan.ai models
  - Ollama manifests (with blob resolution)
- Hugging Face Hub integration for model browsing and download
- Search, filtering, and GGUF file identification
- Authenticated access for private models via HF token
- Download progress tracking and cancellation
- Local model deletion (LLMLaunchpad directory only)

## Non-Functional Requirements

### Performance
- Must run efficiently on target hardware:
  - Windows laptop with 8GB VRAM and 24GB RAM
  - Comparable Mac and Linux specifications
- Target latency: <100ms for UI interactions
- Target throughput: >10 tokens/second for 7B models on target hardware
- Memory usage: <2GB RAM for application overhead (excluding model VRAM)
- Startup time: <5 seconds from launch to usable interface
- Service shutdown: <2 seconds for clean termination

### Compatibility
- Operating Systems:
  - Windows 10+ (64-bit)
  - macOS 12+ (Monterey+) on Intel and Apple Silicon
  - Linux distributions with glibc 2.28+ (Ubuntu 20.04+, RHEL 8+, etc.)
- Hardware Requirements:
  - Minimum: 8GB RAM, 2GB VRAM (CPU-only fallback available)
  - Recommended: 16GB RAM, 6GB VRAM for comfortable 7B model usage
  - No GPU required (CPU-only mode must function correctly)
- Supported Model Formats: GGUF only (quantized Llama, Mistral, Phi, etc.)

### Reliability
- Graceful degradation when components fail:
  - If GPU detection fails, fall back to CPU-only mode with warning
  - If Hugging Face is unreachable, allow local model usage
  - If LiteLLM fails to start, continue with local inference only
- Automatic recovery from common failure states:
  - Stale llama.cpp processes
  - Corrupted configuration files
  - Database lock situations
- Comprehensive error logging with actionable messages
- No silent failures - all errors must be communicated to user

### Security
- All network communications via localhost (127.0.0.1)
- No telemetry or data collection without explicit consent
- Model files stored only in user-accessible directories
- Hugging Face tokens stored securely in user config
- No automatic execution of downloaded models
- Sandboxed service processes where possible
- Input validation on all API endpoints

### Maintainability
- Modular architecture with clear separation of concerns
- Well-documented APIs and interfaces
- Comprehensive error handling throughout
- Consistent code styling and formatting
- Minimal third-party dependencies
- Clear upgrade paths for configuration and data schemas
- Automated build and installation scripts

## User Experience Requirements

### Onboarding
- First-time launch guided setup experience
- Automatic hardware detection and performance mode recommendation
- Model discovery from local sources on first launch
- Clear explanation of performance modes and their tradeoffs
- Optional component installation (Hugging Face, LiteLLM, GPU support)

### Daily Usage
- One-click startup/shutdown of AI services
- Intuitive model selection with clear naming and size information
- Real-time feedback during model loading and inference
- Unobtrusive status indicators that don't distract from chat
- Keyboard shortcuts for common actions (new chat, send, stop generation)
- Responsive design that works on various screen sizes
- Dark/light theme support via system preferences or manual toggle

### Model Management
- Clear visual distinction between local and downloadable models
- Model metadata display (size, quantization, architecture, source)
- Download progress with speed, ETA, and size information
- Ability to pause/resume downloads
- Local model organization and deletion capabilities
- Source attribution for scanned models

### Chat Experience
- Streaming token display with smooth rendering
- Message timestamps and role indicators
- Copy-to-clipboard functionality for individual messages
- Regenerate last response option
- Stop generation button during streaming
- Message editing and retry capabilities
- Conversation search with highlighting
- Export preservation of formatting and metadata

### Advanced Features
- Performance mode switching without service restart (where possible)
- Manual GPU layer adjustment for power users
- Context size configuration
- System prompt customization
- API key management for cloud providers
- Log level adjustment and filtering
- Service restart with current settings preservation

## Technical Constraints

### Architecture Constraints
- No Electron or similar webview wrappers (use Tauri only)
- No Docker dependency for core functionality
- No WebUI derivatives or forks
- Backend must be Python-based
- Frontend must be Svelte + Vite + Tailwind
- Database must be SQLite with FTS5 for search
- Configuration must be file-based (JSON/pyproject.toml)

### Resource Constraints
- Application binary size: <100MB compressed installer
- Runtime memory overhead: <500MB (excluding model VRAM)
- Disk usage for app data: <1GB excluding models
- Network usage: Only for model downloads and optional cloud routing
- No background services when application is not running

### Implementation Constraints
- Phased delivery approach as outlined in AGENTS.md
- No speculative or placeholder implementations
- Error handling must be implemented for all user-facing features
- All features must be tested on target platforms
- Documentation must accompany all user-facing features
- Code must follow established patterns in the existing codebase

### Dependency Constraints
- Backend Python dependencies must be installable via pip
- Frontend dependencies must be installable via npm/yarn
- Prefer well-maintained, actively developed libraries
- Avoid GPL-licensed components that would require source disclosure
- Native binaries (llama.cpp) must be redistributable per their license
- Optional components must have clear installation paths

## Success Criteria

### Minimum Viable Product
A user should be able to:
1. Launch the application (desktop or web)
2. Detect available hardware and select a performance mode
3. Choose a GGUF model from local sources or download from Hugging Face
4. Start the inference service with one click
5. Send a message and receive a streaming response
6. View conversation history and search past messages
7. Export conversations in JSON or Markdown format
8. Monitor service status and logs in real time
9. Stop the service when finished

### Quality Benchmarks
- Application launches successfully on target platforms in <95% of attempts
- Chat latency averages <500ms for first token, <100ms for subsequent tokens
- Zero data loss in conversation history under normal operation
- <1% crash rate during normal usage patterns
- Successful model download and usage from Hugging Face Hub
- Correct GPU layer calculation resulting in stable inference
- Proper cleanup of resources on application exit

### User Adoption Indicators
- Positive feedback on installation and setup experience
- Regular usage patterns indicating sustained value
- Successful model switching without application restart
- Effective search and export of conversation history
- Minimal support requests for basic functionality
- Successful operation in offline mode (after initial model download)