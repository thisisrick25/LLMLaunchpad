---
phase: 0-foundation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: false
requirements: []
user_setup: []

must_haves:
  truths:
    - "All development environment prerequisites are verified"
    - "Installation scripts work correctly on all target platforms"
    - "Initial build and run processes succeed"
    - "Project structure matches the specification"
  artifacts:
    - path: "scripts/install.sh"
      provides: "Unix/macOS installation script"
      min_lines: 50
    - path: "scripts/install.ps1"
      provides: "Windows installation script"
      min_lines: 50
    - path: "scripts/dev.sh"
      provides: "Unix/macOS development script"
      min_lines: 20
    - path: "scripts/dev.ps1"
      provides: "Windows development script"
      min_lines: 20
    - path: "scripts/build.sh"
      provides: "Unix/macOS build script"
      min_lines: 20
    - path: "scripts/build.ps1"
      provides: "Windows build script"
      min_lines: 20
    - path: "app/src-tauri/Cargo.toml"
      provides: "Tauri Rust project configuration"
      contains: '[package]'
    - path: "app/src-tauri/tauri.conf.json"
      provides: "Tauri configuration"
      contains: '"tauri":'
    - path: "app/package.json"
      provides: "Frontend project configuration"
      contains: '"dependencies"'
    - path: "server/pyproject.toml"
      provides: "Backend project configuration"
      contains: '[project]'
  key_links:
    - from: "scripts/install.sh"
      to: "app/src-tauri/Cargo.toml"
      via: "Checks for Rust/Tauri prerequisites"
      pattern: "rustc|cargo|tauri"
    - from: "scripts/install.ps1"
      to: "app/src-tauri/Cargo.toml"
      via: "Checks for Rust/Tauri prerequisites"
      pattern: "rustc|cargo|tauri"
    - from: "scripts/dev.sh"
      to: "app/package.json"
      via: "Runs npm dev command"
      pattern: "npm run dev"
    - from: "scripts/dev.ps1"
      to: "app/package.json"
      via: "Runs npm dev command"
      pattern: "npm run dev"
    - from: "scripts/build.sh"
      to: "app/package.json"
      via: "Runs npm build command"
      pattern: "npm run build"
    - from: "scripts/build.ps1"
      to: "app/package.json"
      via: "Runs npm build command"
      pattern: "npm run build"
---

<objective>
Verify that Phase 0 (Foundation & Project Setup) is complete and ready for Phase 1.
Purpose: Ensure all foundational elements are in place before proceeding with core infrastructure implementation.
Output: Verification report confirming Phase 0 completion.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
@$HOME/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@app/src-tauri/Cargo.toml
@app/src-tauri/tauri.conf.json
@app/package.json
@server/pyproject.toml
@scripts/install.sh
@scripts/install.ps1
@scripts/dev.sh
@scripts/dev.ps1
@scripts/build.sh
@scripts/build.ps1
</context>

<tasks>

<task type="auto">
  <name>Task 1: Verify project structure matches specification</name>
  <files>app/src-tauri/Cargo.toml, app/src-tauri/tauri.conf.json, app/package.json, server/pyproject.toml</files>
  <action>
    Verify that all required project files exist and contain expected configuration:
    - Check app/src-tauri/Cargo.toml for Tauri v2 dependencies
    - Check app/src-tauri/tauri.conf.json for window configuration and permissions
    - Check app/package.json for Svelte, Vite, and Tailwind dependencies
    - Check server/pyproject.toml for FastAPI and required dependencies
    - Verify folder structure matches AGENTS.md specification
  </action>
  <verify>
    ls -la app/src-tauri/ && ls -la app/src/ && ls -la server/src/ && ls -la scripts/
  </verify>
  <done>
    All required project files exist with correct basic structure as specified in AGENTS.md and ROADMAP.md
  </done>
</task>

<task type="auto">
  <name>Task 2: Verify installation scripts functionality</name>
  <files>scripts/install.sh, scripts/install.ps1</files>
  <action>
    Verify installation scripts contain necessary checks and setup procedures:
    - Check for prerequisite validation (Node.js, Python, Rust, etc.)
    - Verify script creates necessary directories (~/.llmlaunchpad/models, data, logs)
    - Confirm scripts are executable and have proper shebangs
    - Validate scripts handle errors appropriately
  </action>
  <verify>
    bash -n scripts/install.sh && pwsh -NoProfile -Command "& { Set-StrictMode -Version Latest; . scripts/install.ps1 -WhatIf }" 2>&1 | head -5
  </verify>
  <done>
    Installation scripts are syntactically correct and contain prerequisite checks and directory creation logic
  </done>
</task>

<task type="auto">
  <name>Task 3: Verify development and build scripts functionality</name>
  <files>scripts/dev.sh, scripts/dev.ps1, scripts/build.sh, scripts/build.ps1</files>
  <action>
    Verify development and build scripts contain correct commands:
    - Check dev.sh and dev.ps1 run frontend and backend development servers
    - Check build.sh and build.ps1 create production builds
    - Verify scripts handle Tauri-specific commands when applicable
    - Confirm scripts are executable
  </action>
  <verify>
    bash -n scripts/dev.sh && bash -n scripts/dev.ps1 && bash -n scripts/build.sh && bash -n scripts/build.ps1
  </verify>
  <done>
    Development and build scripts are syntactically correct and contain appropriate npm and cargo commands
  </done>
</task>

<task type="checkpoint:human-verify">
  <name>Task 4: Human verification of Phase 0 completion</name>
  <files></files>
  <action>
    Manually verify that Phase 0 foundation is complete by:
    1. Checking that all required files exist in correct locations
    2. Verifying installation scripts can be parsed without syntax errors
    3. Confirming development and build scripts are syntactically valid
    4. Validating that project structure matches the specification in AGENTS.md
    5. Ensuring all scripts have appropriate shebangs and are executable (where applicable)
  </action>
  <verify>
    Type "approved" when manual verification is complete
  </verify>
  <done>
    Human verifier has confirmed Phase 0 foundation is complete and ready for Phase 1
  </done>
</task>

</tasks>

<verification>
Overall verification that Phase 0 foundation is complete and ready for Phase 1 development
</verification>

<success_criteria>
All must_haves truths are verified:
- Development environment prerequisites are verified through script checks
- Installation scripts work correctly on all target platforms (syntactically valid)
- Initial build and run processes can succeed (scripts contain correct commands)
- Project structure matches the specification (all required files present)
</success_criteria>

<output>
After completion, create .planning/phases/0-foundation/0-foundation-01-SUMMARY.md
</output>