# LLMLaunchpad - Development Script (Windows)

param(
[switch]$Tauri,
[switch]$Help
)

$ErrorActionPreference = "Stop"

# Change to project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Set dev environment variable
$env:LLMLAUNCHPAD_DEV = "1"

if ($Help) {
Write-Host "Usage: dev.ps1 [OPTIONS]"
Write-Host ""
Write-Host "Options:"
Write-Host " -Tauri Run Tauri desktop app instead of web"
Write-Host " -Help Show this help message"
Write-Host ""
Write-Host "Default: Runs web app + backend"
exit 0
}

# Check if dependencies are installed
if (-not (Test-Path "server\.venv")) {
Write-Host "Error: Backend not installed." -ForegroundColor Red
Write-Host "Run .\scripts\install.ps1 first."
exit 1
}

if (-not (Test-Path "app\node_modules")) {
Write-Host "Error: Frontend not installed." -ForegroundColor Red
Write-Host "Run .\scripts\install.ps1 first."
exit 1
}

# Run dev model check
Write-Host "Checking for development model..." -ForegroundColor Cyan
Write-Host ""
python scripts/get-dev-model.py
$devModelExit = $LASTEXITCODE
Write-Host ""

# Get model path for display
$modelPath = "$env:USERPROFILE\.llmlaunchpad\models\dev\Phi-3-mini-4k-instruct-q4.gguf"

# Start servers
if ($Tauri) {
# Check for Rust
$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if (-not $cargo) {
Write-Host "Error: Rust/Cargo is required for Tauri mode." -ForegroundColor Red
Write-Host "Install from https://rustup.rs"
exit 1
}

Write-Host "=================================================="
Write-Host "Dev model check complete."
if ($devModelExit -eq 0 -or $devModelExit -eq 2) {
    Write-Host "Model location: $modelPath"
}
Write-Host "Starting development servers (Tauri mode)..."
Write-Host "=================================================="
Write-Host ""
npm run dev:tauri
} else {
Write-Host "=================================================="
Write-Host "Dev model check complete."
if ($devModelExit -eq 0 -or $devModelExit -eq 2) {
    Write-Host "Model location: $modelPath"
}
Write-Host "Starting development servers..."
Write-Host "=================================================="
Write-Host ""
Write-Host "Web UI: http://localhost:5173" -ForegroundColor Green
Write-Host "API: http://localhost:8000" -ForegroundColor Green
Write-Host ""
npm run dev
}
