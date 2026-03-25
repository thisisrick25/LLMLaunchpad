# LLMLaunchpad - Build Script (Windows)

param(
    [switch]$Tauri,
    [switch]$All,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Change to project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

if ($Help) {
    Write-Host "Usage: build.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Tauri    Build Tauri desktop app only"
    Write-Host "  -All      Build both web and Tauri"
    Write-Host "  -Help     Show this help message"
    Write-Host ""
    Write-Host "Default: Builds web app only (app\dist\)"
    exit 0
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  LLMLaunchpad Build" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if dependencies are installed
if (-not (Test-Path "app\node_modules")) {
    Write-Host "Error: Frontend not installed." -ForegroundColor Red
    Write-Host "Run .\scripts\install.ps1 first."
    exit 1
}

function Build-Web {
    Write-Host "Building web app..." -ForegroundColor Cyan
    Push-Location app
    npm run build
    Pop-Location
    Write-Host "Web build complete: app\dist\" -ForegroundColor Green
}

function Build-Tauri {
    # Check for Rust
    $cargo = Get-Command cargo -ErrorAction SilentlyContinue
    if (-not $cargo) {
        Write-Host "Error: Rust/Cargo is required for Tauri build." -ForegroundColor Red
        Write-Host "Install from https://rustup.rs"
        exit 1
    }
    
    Write-Host "Building Tauri desktop app..." -ForegroundColor Cyan
    Push-Location app
    npm run tauri:build
    Pop-Location
    Write-Host "Tauri build complete: app\src-tauri\target\release\" -ForegroundColor Green
    
    # Show output files
    Write-Host ""
    Write-Host "Build artifacts:" -ForegroundColor Cyan
    $bundlePath = "app\src-tauri\target\release\bundle"
    if (Test-Path $bundlePath) {
        Get-ChildItem -Path $bundlePath -Recurse -Include "*.exe", "*.msi" | ForEach-Object {
            $size = "{0:N2} MB" -f ($_.Length / 1MB)
            Write-Host "  $($_.FullName) ($size)" -ForegroundColor Green
        }
    }
}

if ($Tauri) {
    Build-Tauri
} elseif ($All) {
    Build-Web
    Write-Host ""
    Build-Tauri
} else {
    Build-Web
}

Write-Host ""
Write-Host "Build complete!" -ForegroundColor Green
