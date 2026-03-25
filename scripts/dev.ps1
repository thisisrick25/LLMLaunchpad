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

if ($Help) {
    Write-Host "Usage: dev.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Tauri    Run Tauri desktop app instead of web"
    Write-Host "  -Help     Show this help message"
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

# Start servers
if ($Tauri) {
    # Check for Rust
    $cargo = Get-Command cargo -ErrorAction SilentlyContinue
    if (-not $cargo) {
        Write-Host "Error: Rust/Cargo is required for Tauri mode." -ForegroundColor Red
        Write-Host "Install from https://rustup.rs"
        exit 1
    }
    
    Write-Host "Starting LLMLaunchpad (Tauri desktop + backend)..." -ForegroundColor Cyan
    Write-Host ""
    npm run dev:tauri
} else {
    Write-Host "Starting LLMLaunchpad (web + backend)..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Web UI: http://localhost:5173" -ForegroundColor Green
    Write-Host "API:    http://localhost:8000" -ForegroundColor Green
    Write-Host ""
    npm run dev
}
