---
phase: 2-local-inference-engine
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true
requirements: [INF-01, INF-02, INF-03, INF-04, INF-05, INF-06]
user_setup: []

must_haves:
  truths:
    - "User can download and verify llama.cpp binary"
    - "User can load and run a GGUF model through the API"
    - "System validates GGUF format before attempting to load"
    - "llama-server process is properly monitored and controlled"
    - "Text generation API returns coherent responses"
    - "Error handling prevents crashes and provides actionable feedback"
  artifacts:
    - path: "server/src/llmlaunchpad/llama.py"
      provides: "Enhanced llama-server management with binary download and verification"
      min_lines: 500
    - path: "server/src/llmlaunchpad/routes/chat.py"
      provides: "Robust text generation API with improved error handling"
      exports: ["POST /chat/completions"]
    - path: "server/src/llmlaunchpad/models.py"
      provides: "GGUF format validation and verification"
      contains: "def validate_gguf_format"
  key_links:
    - from: "server/src/llmlaunchpad/routes/chat.py"
      to: "server/src/llmlaunchpad/llama.py"
      via: "get_llama_server() calls"
      pattern: "get_llama_server"
    - from: "server/src/llmlaunchpad/llama.py"
      to: "server/src/llmlaunchpad/models.py"
      via: "Model validation before loading"
      pattern: "validate_gguf_format"
---

<objective>
Enhance the local inference engine integration to provide reliable llama.cpp binary management, robust model loading, and reliable text generation capabilities.

Purpose: Enable users to download, verify, and run local GGUF models with proper error handling and process management.
Output: A production-ready local inference engine integration that handles binary management, model validation, and reliable text generation.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
@$HOME/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/0-foundation/0-foundation-01-SUMMARY.md
@.planning/phases/1-core-infrastructure/1-core-infrastructure-01-SUMMARY.md
@app/src/lib/store.ts
@app/src/features/chat/chat.ts
@server/src/llmlaunchpad/llama.py
@server/src/llmlaunchpad/routes/chat.py
@server/src/llmlaunchpad/models.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add llama.cpp binary download and verification</name>
  <files>server/src/llmlaunchpad/llama.py</files>
  <action>
    Enhance the find_llama_server function to include binary download capability when not found. Add:
    1. Download function that fetches appropriate llama-server binary based on platform from official releases
    2. Verification of downloaded binary (checksum, executable permissions)
    3. Config option to specify binary source or disable auto-download
    4. Progress reporting during download
    5. Fallback to user-specified path if download fails
    Reference: RECOMMENDED_MODELS from models.py for version guidance
    Per D-01: Use official llama.cpp releases from github.com/ggerganov/llama.cpp
  </action>
  <verify>
    <automated>python -m pytest server/tests/ -xvs -k test_llama_binary_download || echo "No test file exists - MISSING — Wave 0 must create server/tests/test_llama_binary.py first"</automated>
  </verify>
  <done>
    Binary download function exists, verifies checksums, sets executable permissions, and integrates with existing find_llama_server flow. User can configure download behavior.
  </done>
</task>

<task type="auto">
  <name>Task 2: Implement GGUF format validation and verification</name>
  <files>server/src/llmlaunchpad/models.py</files>
  <action>
    Add GGUF format validation functions to prevent attempting to load invalid models:
    1. validate_gguf_format(file_path) -> bool that checks GGUF magic number and version
    2. extract_gguf_metadata(file_path) that reads model size, tensor info, etc.
    3. Integrate validation into find_model_by_name and scan functions
    4. Add caching of validation results to avoid repeated file reads
    5. Provide detailed error messages for invalid GGUF files
    Per D-02: Only GGUF format is supported; reject other formats with clear error messages
  </action>
  <verify>
    <automated>python -m pytest server/tests/ -xvs -k test_gguf_validation || echo "No test file exists - MISSING — Wave 0 must create server/tests/test_gguf_validation.py first"</automated>
  </verify>
  <done>
    GGUF validation function exists, correctly identifies valid/invalid GGUF files, extracts metadata, and is integrated into model loading flow. Invalid formats are rejected with clear error messages.
  </done>
</task>

<task type="auto">
  <name>Task 3: Enhance text generation API with robust error handling</name>
  <files>server/src/llmlaunchpad/routes/chat.py</files>
  <action>
    Improve the chat completion endpoints to handle errors gracefully:
    1. Add timeout handling for llama-server requests (both connect and read timeouts)
    2. Implement retry logic for transient failures (with exponential backoff)
    3. Provide detailed error responses including llama-server stderr when available
    4. Add validation of request parameters before forwarding to llama-server
    5. Implement circuit breaker pattern to prevent cascading failures
    6. Log all errors with context for debugging
    Per D-03: Never expose internal server errors directly to users; always provide actionable messages
  </action>
  <verify>
    <automated>python -m pytest server/tests/ -xvs -k test_chat_error_handling || echo "No test file exists - MISSING — Wave 0 must create server/tests/test_chat_errors.py first"</automated>
  </verify>
  <done>
    Chat API handles timeouts, retries transient failures, validates inputs, provides actionable error messages, and implements circuit breaker pattern. All errors are logged with context.
  </done>
</task>

</tasks>

<verification>
Verify that the local inference engine integration works end-to-end:
1. Binary downloads successfully for current platform
2. GGUF validation correctly accepts valid models and rejects invalid ones
3. Text generation API returns coherent responses for valid prompts
4. Error handling provides actionable feedback without crashing
5. Process monitoring shows correct server states throughout lifecycle
</verification>

<success_criteria>
- llama.cpp binary can be downloaded and verified automatically
- Valid GGUF models load successfully and generate coherent text
- Invalid or corrupted GGUF files are rejected with clear error messages
- Text generation API handles timeouts, retries, and errors gracefully
- llama-server process state is accurately tracked and reported
- All new functionality is covered by automated tests
</success_criteria>

<output>
After completion, create .planning/phases/2-local-inference-engine/2-local-inference-engine-01-SUMMARY.md
</output>