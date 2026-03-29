---
phase: 1-core-infrastructure
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true
requirements: [1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
user_setup: []

must_haves:
  truths:
    - "Backend service starts and stops successfully via API"
    - "Frontend can connect to backend and display system status"
    - "Hardware detection works cross-platform and shows CPU, RAM, GPU info"
    - "Configuration persists between application sessions"
    - "Service health monitoring reflects actual backend state"
  artifacts:
    - path: "server/src/llmlaunchpad/main.py"
      provides: "FastAPI application entry point"
      exports: ["app"]
    - path: "server/src/llmlaunchpad/routes/control.py"
      provides: "Service lifecycle endpoints (/start, /stop, /restart, /mode, /logs)"
      exports: ["router"]
    - path: "server/src/llmlaunchpad/routes/status.py"
      provides: "System status and hardware endpoints"
      exports: ["router"]
    - path: "server/src/llmlaunchpad/hardware.py"
      provides: "Cross-platform hardware detection"
      exports: ["detect_hardware", "get_hardware_info"]
    - path: "server/src/llmlaunchpad/config.py"
      provides: "Configuration persistence system"
      exports: ["get_config", "save_config", "Config"]
    - path: "app/src/App.svelte"
      provides: "Main application UI integrating backend status and controls"
      exports: ["default"]
    - path: "app/src/features/services/ServiceControls.svelte"
      provides: "UI for starting/stopping backend service"
      exports: ["default"]
    - path: "app/src/features/services/StatusBar.svelte"
      provides: "UI for displaying system hardware and service status"
      exports: ["default"]
    - path: "app/src/shared/api.ts"
      provides: "Frontend API client for backend communication"
      exports: ["api"]
    - path: "app/src-tauri/tauri.conf.json"
      provides: "Tauri desktop application configuration"
      exports: ["tauri configuration"]
  key_links:
    - from: "app/src/App.svelte"
      to: "/api/status"
      via: "api.getStatus() call in onMount"
      pattern: "request.*/status"
    - from: "app/src/App.svelte"
      to: "/api/hardware"
      via: "api.getHardware() call (through status endpoint)"
      pattern: "request.*/hardware"
    - from: "app/src/features/services/ServiceControls.svelte"
      to: "/api/control/start"
      via: "api.startServer() call"
      pattern: "request.*/control/start"
    - from: "app/src/features/services/ServiceControls.svelte"
      to: "/api/control/stop"
      via: "api.stopServer() call"
      pattern: "request.*/control/stop"
    - from: "app/src/features/services/ServiceControls.svelte"
      to: "/api/control/mode"
      via: "api.setMode() call"
      pattern: "request.*/control/mode"
    - from: "app/src/features/services/StatusBar.svelte"
      to: "hardware prop"
      via: "bound hardware prop from App.svelte"
      pattern: "export let hardware"
    - from: "server/src/llmlaunchpad/config.py"
      to: "server/src/llmlaunchpad/main.py"
      via: "get_config() call in startup event"
      pattern: "from .config import get_config"
    - from: "server/src/llmlaunchpad/main.py"
      to: "server/src/llmlaunchpad/routes/__init__.py"
      via: "app.include_router(router)"
      pattern: "app.include_router.*router"
---

<objective>
Implement the core infrastructure for service management including backend API endpoints, frontend UI for service controls, and cross-platform hardware detection.

Purpose: Establish the foundation for starting/stopping the AI service and displaying system information
Output: Working backend service lifecycle endpoints, desktop/web UI with service controls, and hardware monitoring
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
@$HOME/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/1-core-infrastructure/1-core-infrastructure-CONTEXT.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Implement backend service lifecycle API endpoints</name>
  <files>server/src/llmlaunchpad/routes/control.py</files>
  <action>Implement the control API routes for starting, stopping, and monitoring the llama-server service including /start, /stop, /restart, /status, /mode, /logs, /health, and /config endpoints with proper error handling and validation. Use existing code as reference but ensure all endpoints are functional.</action>
  <verify>python -m pytest server/tests/ -v -k "control" || echo "No specific test file exists; manual verification: start server with POST /control/start, check status with GET /control/stop, stop server with POST /control/stop"</verify>
  <done>Backend service can be started, stopped, and restarted via API endpoints with proper responses and error handling</done>
</task>

<task type="auto">
  <name>Task 2: Implement frontend service controls and status display</name>
  <files>app/src/features/services/ServiceControls.svelte, app/src/features/services/StatusBar.svelte, app/src/App.svelte</files>
  <action>Create or update the ServiceControls.svelte component to provide UI for starting/stopping service and selecting models, StatusBar.svelte to display hardware and service status, and integrate both into App.svelte with proper state management and API calls via the shared api.ts module.</action>
  <verify>npm run dev -- --port 5173 & npx wait-on http://localhost:5173 && echo "Manual verification: Check that Service Controls and Status Bar are visible in the UI and respond to user interactions"</verify>
  <done>Frontend displays service controls and status bar, can start/stop service via UI, and shows hardware information</done>
</task>

<task type="auto">
  <name>Task 3: Verify cross-platform hardware detection and configuration persistence</name>
  <files>server/src/llmlaunchpad/hardware.py, server/src/llmlaunchpad/config.py, server/src/llmlaunchpad/main.py, server/src/llmlaunchpad/routes/status.py</files>
  <action>Ensure hardware detection works correctly across Windows, macOS, and Linux by testing the detect_hardware() function, verify configuration persistence through get_config() and save_config() functions, and confirm that startup/shutdown sequences properly initialize and save configuration.</action>
  <verify>python -c "from server.src.llmlaunchpad.hardware import detect_hardware; from server.src.llmlaunchpad.config import get_config, save_config; print('Hardware detection:', detect_hardware()); print('Config loading:', get_config())" && echo "Manual verification: Check that hardware info appears in UI and settings persist between sessions"</verify>
  <done>Hardware detection returns system information on all platforms and configuration persists between application restarts</done>
</task>

</tasks>

<verification>
Verify that all Phase 1 deliverables are complete:
- Backend API endpoints are functional and tested
- Frontend UI shows service controls and hardware status
- Cross-platform hardware detection works
- Configuration persists between sessions
</verification>

<success_criteria>
User can launch the application, see system information (CPU, RAM, GPU), start/stop the backend service through the UI, and have their settings persist between sessions.
</success_criteria>

<output>
After completion, create .planning/phases/1-core-infrastructure/1-core-infrastructure-01-SUMMARY.md
</output>