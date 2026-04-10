---
phase: 5-performance-controls
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/src/llmlaunchpad/offload.py
  - server/src/llmlaunchpad/routes/control.py
  - app/src/features/services/services.ts
  - app/src/features/services/ServiceControls.svelte
  - app/src/shared/types.ts
autonomous: true
requirements: [PERF-01, PERF-02, PERF-03, PERF-04, PERF-05]

must_haves:
  truths:
    - "User can select from four performance modes: Auto, GPU-Heavy, CPU-Only, Cloud"
    - "System automatically calculates optimal GPU layers based on VRAM and model size in Auto mode"
    - "VRAM usage is monitored and validated to prevent OOM conditions"
    - "Manual GPU layer overrides work for advanced users"
    - "Performance mode changes take effect immediately or with clear restart guidance"
  artifacts:
    - path: "server/src/llmlaunchpad/offload.py"
      provides: "GPU layer calculation logic with safety margins"
      min_lines: 50
    - path: "server/src/llmlaunchpad/routes/control.py"
      provides: "API endpoints for performance mode control and status"
      exports: ["GET /control/mode", "POST /control/mode", "GET /control/config"]
    - path: "app/src/features/services/services.ts"
      provides: "Frontend state management for performance modes"
      min_lines: 30
    - path: "app/src/features/services/ServiceControls.svelte"
      provides: "UI controls for performance mode selection and manual overrides"
      min_lines: 40
  key_links:
    - from: "app/src/features/services/ServiceControls.svelte"
      to: "/control/mode"
      via: "servicesStore.setMode()"
      pattern: "api.setMode"
    - from: "server/src/llmlaunchpad/routes/control.py"
      to: "server/src/llmlaunchpad/offload.py"
      via: "calculate_offload function call"
      pattern: "calculate_offload"
    - from: "app/src/features/services/services.ts"
      to: "app/src/shared/types.ts"
      via: "OffloadRecommendation type usage"
      pattern: "OffloadRecommendation"
---

<objective>
Enhance performance controls and hardware optimization to provide users with intelligent GPU/CPU offloading, multiple performance modes, and safe defaults for optimal local AI execution across different hardware configurations.

Purpose: Enable users to maximize performance based on their specific hardware while preventing system instability from OOM conditions.
Output: A cohesive performance control system that automatically optimizes settings while providing manual override capabilities.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
@$HOME/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/STATE.md
@app/src/features/services/ServiceControls.svelte
@app/src/features/services/services.ts
@/server/src/llmlaunchpad/offload.py
@/server/src/llmlaunchpad/routes/control.py
@/app/src/shared/types.ts
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Enhance offload calculation with improved safety margins and validation</name>
  <files>server/src/llmlaunchpad/offload.py</files>
  <behavior>
    - Test 1: calculate_offload returns gpu_layers=0 when no GPU detected
    - Test 2: calculate_offload respects CPU-only mode setting
    - Test 3: calculate_offload respects Cloud mode setting
    - Test 4: calculate_offload applies appropriate safety margins for Auto vs GPU-Heavy modes
    - Test 5: calculate_offload prevents OOM by validating against total available VRAM
    - Test 6: calculate_offload handles edge cases (very small/large models, extreme VRAM values)
  </action>
  Enhance the offload.py module to improve safety and reliability:
  1. Refine safety margin calculations - use more conservative values for Auto mode (0.75) vs GPU-Heavy (0.9)
  2. Add explicit VRAM validation to prevent allocating more layers than physically possible
  3. Improve context memory estimation to be more accurate for different model architectures
  4. Add logging for offload calculation decisions for debugging
  5. Ensure the function handles edge cases gracefully (extremely large models, zero VRAM scenarios)
  6. Add validation that calculated gpu_layers never exceeds the model's actual layer count
  7. Improve the reason strings to be more informative about why certain settings were chosen
</task>

<task type="auto">
  <name>Task 2: Implement performance mode switching without restart where possible</name>
  <files>server/src/llmlaunchpad/routes/control.py, server/src/llmlaunchpad/llama.py</files>
  <action>
  Implement dynamic performance mode switching that avoids service restarts when feasible:
  1. Add a new endpoint /control/optimize that recalculates and applies optimal GPU layers for current model without full restart
  2. Modify the setMode endpoint to detect when a mode change can be applied dynamically (when switching between Auto/GPU-Heavy/CPU-Only with same model)
  3. Enhance LlamaServer class to support dynamic GPU layer updates via llama-server API or SIGHUP where supported
  4. When dynamic update isn't possible, provide clear guidance that a restart is required
  5. Add validation to prevent unsafe mode transitions (e.g., Cloud to local when no model loaded)
  6. Update the ModeRequest model to include optional force_restart parameter for advanced users
  7. Ensure proper error handling and status reporting for optimization attempts
</action>
<verify>
  python -m pytest server/tests/ -xvs -k "test_offload or test_control" || echo "No specific tests found; manual verification required"
</verify>
<done>
  - Performance mode switching between Auto/GPU-Heavy/CPU-Only works without restart when same model is loaded
  - System provides clear feedback when restart is required for mode changes
  - Dynamic optimization endpoint successfully recalculates and applies better GPU layer settings
  - All existing mode switching functionality continues to work as expected
</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Enhance frontend performance controls with manual overrides and monitoring</name>
  <files>app/src/features/services/services.ts, app/src/features/services/ServiceControls.svelte, app/src/shared/types.ts</files>
  <behavior>
    - Test 1: servicesStore correctly handles manual GPU layer overrides
    - Test 2: ServiceControls UI shows manual override controls when advanced options are enabled
    - Test 3: Manual GPU layer input validates against reasonable ranges (0-200)
    - Test 4: VRAM monitoring displays real-time usage and availability
    - Test 5: Performance mode descriptions update correctly based on selected mode
    - Test 6: Manual overrides persist across sessions when saved to config
  </action>
  Enhance the frontend performance controls to provide better user experience and monitoring:
  1. Extend services.ts to manage manual GPU layer overrides alongside performance modes
  2. Add VRAM monitoring to services.ts that polls hardware status periodically
  3. Enhance ServiceControls.svelte with:
     - Manual GPU layer input field (visible in advanced options)
     - Real-time VRAM usage display
     - Visual indicators when manual overrides are active
     - Tooltips explaining the implications of different settings
     - Validation to prevent obviously unsafe manual inputs
  4. Update shared/types.ts to include new fields for manual override tracking
  5. Ensure manual overrides are properly sent to the backend when starting server
  6. Add visual feedback when performance mode changes are applied vs requiring restart
</action>
<verify>
  npm test -- --test-name-pattern="performance.*control|service.*mode" || echo "No specific frontend tests found; manual verification required"
</verify>
<done>
  - Users can manually override GPU layer count in advanced options
  - Real-time VRAM monitoring shows current usage and availability
  - Manual overrides are validated to prevent unsafe values
  - Clear visual indication when manual overrides are active
  - Performance mode changes provide appropriate feedback about restart requirements
  - Manual overrides persist across application sessions
</done>
</task>

</tasks>

<verification>
Verify that the performance control system works cohesively:
1. Starting server in Auto mode calculates reasonable GPU layers based on detected VRAM
2. Switching to GPU-Heavy mode increases GPU utilization appropriately
3. Switching to CPU-Only mode sets GPU layers to 0
4. Switching to Cloud mode disables local inference
5. Manual overrides work and persist across sessions
6. VRAM monitoring displays accurate information
7. Performance mode changes provide clear guidance about restart requirements
</verification>

<success_criteria>
Users can successfully:
- Select from all four performance modes (Auto, GPU-Heavy, CPU-Only, Cloud)
- See accurate VRAM monitoring information in the UI
- Use manual GPU layer overrides for fine-tuning
- Experience appropriate performance mode switching behavior (with or without restart)
- Trust that the system prevents OOM conditions through safe defaults
- Understand when performance mode changes require a service restart
</success_criteria>

<output>
After completion, create .planning/phases/5-performance-controls/5-performance-controls-01-SUMMARY.md
</output>