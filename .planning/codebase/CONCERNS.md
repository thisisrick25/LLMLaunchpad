# Codebase Concerns

**Analysis Date:** 2026-03-28

## Tech Debt

**[Hardware Detection - GPU Support]:**
- Issue: Incomplete GPU detection - only NVIDIA GPUs via GPUtil are supported; AMD ROCm and Apple Metal detection are missing.
- Files: `server/src/llmlaunchpad/hardware.py`
- Impact: Users with AMD or Apple Silicon GPUs cannot leverage GPU acceleration for llama.cpp, forcing CPU-only inference which is significantly slower.
- Fix approach: Implement GPU detection for AMD (using ROCm or similar) and Apple (using Metal) platforms. Add fallback mechanisms when platform-specific libraries aren't available.

**[Dependency Management]:**
- Issue: Hardware detection depends on GPUtil package for NVIDIA detection, which is an optional dependency but not explicitly documented as required for GPU functionality.
- Files: `server/src/llmlaunchpad/hardware.py`, `pyproject.toml`
- Impact: Users may not have GPUtil installed, leading to silent failure of GPU detection and suboptimal performance.
- Fix approach: Document GPUtil as a required dependency for GPU detection, or implement alternative detection methods (like nvidia-smi parsing) that don't require external packages.

## Known Bugs

**[Hardware Info Caching]:**
- Symptoms: Hardware information is cached globally, potentially returning stale data if hardware configuration changes (e.g., external GPU connected/disconnected).
- Files: `server/src/llmlaunchpad/hardware.py` (lines 132-140)
- Trigger: Changes in GPU availability during application runtime.
- Workaround: None currently; requires application restart to refresh hardware info.
- Fix approach: Add manual refresh capability via API endpoint, or implement periodic hardware polling for significant changes.

## Security Considerations

**[API Key Handling]:**
- Risk: LiteLLM integration expects API keys as environment variables; potential for accidental exposure through logs or error messages.
- Files: `server/src/llmlaunchpad/litellm.py` (lines 188-194)
- Current mitigation: API keys are retrieved from environment variables and not hardcoded.
- Recommendations: 
  - Ensure API keys are never logged or included in error responses.
  - Consider implementing environment variable validation at startup.
  - Add runtime checks to prevent logging of sensitive configuration.

**[Process Management]:**
- Risk: llama.cpp service management involves spawning and terminating external processes; improper handling could leave orphaned processes.
- Files: `server/src/llmlaunchpad/llama.py`
- Current mitigation: Basic process tracking and cleanup on stop.
- Recommendations: 
  - Implement robust process group management to ensure child processes are terminated.
  - Add timeout handling for process termination to prevent hangs.

## Performance Bottlenecks

**[Model Scanning]:**
- Problem: Model scanner checks multiple directories (LLMLaunchpad, LM Studio, HF Cache, GPT4All, Jan, Ollama) on every request, which could be slow with large model collections.
- Files: `server/src/llmlaunchpad/models.py`
- Cause: I/O operations across multiple filesystem locations without caching.
- Improvement path: 
  - Implement caching of model scan results with invalidation triggers (e.g., file system watchers or timed refresh).
  - Allow users to configure which directories to scan to reduce overhead.
  - Consider incremental scanning rather than full rescans.

**[Chat History Retrieval]:**
- Problem: As chat history grows, database queries for conversations and messages may slow down, especially with full-text search.
- Files: `server/src/llmlaunchpad/database.py`, `server/src/llmlaunchpad/routes/conversations.py`
- Cause: SQLite FTS5 is efficient but may degrade with very large datasets (>100K messages).
- Improvement path:
  - Add pagination to conversation and message lists.
  - Implement archive/pruning policies for very old conversations.
  - Consider adding indices on frequently queried columns.

## Fragile Areas

**[External Process Dependencies]:**
- Files: `server/src/llmlaunchpad/llama.py`, `server/src/llmlaunchpad/litellm.py`
- Why fragile: Functionality depends on external executables (llama-server, litellm) being available and compatible.
- Safe modification: 
  - Validate external dependencies at startup and provide clear error messages.
  - Version check compatibility where possible.
  - Implement fallback mechanisms (e.g., bundled binaries or version-specific behavior).
- Test coverage: Integration tests for external process spawning are limited; unit tests mock these dependencies.

**[Configuration Persistence]:**
- Files: `server/src/llmlaunchpad/config.py`
- Why fragile: Configuration is stored in a single JSON file; corruption or concurrent writes could lead to data loss.
- Safe modification: 
  - Implement file locking or atomic writes.
  - Add configuration schema validation and migration strategies.
  - Consider using a proper configuration database (though SQLite is already used for chats).

## Scaling Limits

**[Concurrent Users]:**
- Current capacity: Designed for single-user desktop application.
- Limit: Multi-user scenarios not supported due to shared model instance and hardware resources.
- Scaling path: 
  - Clearly document single-user limitation.
  - For multi-user needs, recommend separate instances or containerized deployments.
  - Consider implementing user isolation if multi-user becomes a requirement.

**[Model Size Limitations]:**
- Current capacity: Limited by available RAM/VRAM; larger models may cause excessive swapping or OOM.
- Limit: Hardware offload calculations assume model fits in memory with GPU layers.
- Scaling path: 
  - Improve offload calculations to account for memory swapping penalties.
  - Add warnings when model size exceeds reasonable thresholds for available hardware.
  - Consider implementing model quantization suggestions based on hardware.

## Dependencies at Risk

**[GPUtil]:**
- Risk: Third-party package for NVIDIA GPU detection; if unmaintained or incompatible with new driver versions, GPU detection fails.
- Impact: Loss of GPU acceleration capabilities for NVIDIA users.
- Migration plan: 
  - Implement alternative detection using nvidia-smi parsing (more stable interface).
  - Add fallback to nvidia-smi when GPUtil fails or is unavailable.
  - Abstract GPU detection behind an interface to allow multiple implementations.

**[LiteLLM]:**
- Risk: Optional cloud routing dependency; if LiteLLM has breaking changes or security issues, affects cloud functionality.
- Impact: Cloud model routing becomes unavailable or insecure.
- Migration plan: 
  - Pin to specific LiteLLM version with known compatibility.
  - Monitor LiteLLM security advisories.
  - Consider implementing direct API calls for major providers as alternative.

## Missing Critical Features

**[Graceful Degradation]:**
- Problem: If llama.cpp fails to start or crashes, the application lacks fallback mechanisms.
- Blocks: Reliable user experience; users may be left without any inference capability.
- Solution: 
  - Implement fallback to cloud models via LiteLLM when local inference fails.
  - Add retry mechanisms with exponential backoff for transient failures.
  - Provide clear user feedback when local services are unavailable.

**[Resource Monitoring]:**
- Problem: No real-time monitoring of resource usage (VRAM, RAM, CPU) during inference to prevent system overload.
- Blocks: Users may experience system instability or crashes with large models.
- Solution: 
  - Add resource monitoring during model loading and inference.
  - Implement automatic offload adjustments based on real-time usage.
  - Provide user-configurable resource limits.

## Test Coverage Gaps

**[Hardware Detection Logic]:**
- What's not tested: AMD and Apple GPU detection paths (currently unimplemented), error cases in GPU detection.
- Files: `server/src/llmlaunchpad/hardware.py`
- Risk: Undetected regressions when adding new GPU detection methods; platform-specific bugs.
- Priority: High (affects core functionality)

**[External Process Failure Scenarios]:**
- What's not tested: llama.cpp startup failures, litellm connection errors, model loading errors.
- Files: `server/src/llmlaunchpad/llama.py`, `server/src/llmlaunchpad/litellm.py`
- Risk: Application may hang or provide poor error messages when external services fail.
- Priority: High (affects reliability)

**[Configuration Edge Cases]:**
- What's not tested: Invalid configuration values, file permission issues, concurrent modification scenarios.
- Files: `server/src/llmlaunchpad/config.py`
- Risk: Configuration corruption leading to application startup failures.
- Priority: Medium