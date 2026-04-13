# LLMLaunchpad - Install Script (Windows)

param(
    [switch]$SkipTauri,
    [switch]$All,
    [switch]$Minimal,
    [switch]$NoPrompt,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Change to project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Data directory
$DataDir = Join-Path $env:USERPROFILE ".llmlaunchpad"
$BinDir = Join-Path $DataDir "bin"

if ($Help) {
    Write-Host "Usage: install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -All          Install all optional components"
    Write-Host "  -Minimal      Install only core (skip all optional)"
    Write-Host "  -NoPrompt     Non-interactive mode (use -All or -Minimal)"
    Write-Host "  -SkipTauri    Skip Rust/Tauri check"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    Write-Host "Optional components:"
    Write-Host "  - llama.cpp     Local inference engine (downloads binary)"
    Write-Host "  - LiteLLM       Cloud model routing (OpenAI, Anthropic, etc.)"
    Write-Host "  - Hugging Face  Model downloads from HF Hub"
    Write-Host "  - GPU support   NVIDIA GPU detection"
    exit 0
}

Write-Host "==========================================" -ForegroundColor White
Write-Host "  LLMLaunchpad Installer" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor White
Write-Host ""

#region Detection Functions
function Test-LlamaCppInstalled {
    # Check in our bin directory
    $localPath = Join-Path $BinDir "llama-server.exe"
    if (Test-Path $localPath) {
        return @{ Installed = $true; Path = $localPath; Source = "LLMLaunchpad" }
    }
    
    # Check in PATH
    $inPath = Get-Command "llama-server" -ErrorAction SilentlyContinue
    if ($inPath) {
        return @{ Installed = $true; Path = $inPath.Source; Source = "PATH" }
    }
    
    # Check common locations
    $commonPaths = @(
        "$env:LOCALAPPDATA\llama.cpp\llama-server.exe",
        "$env:ProgramFiles\llama.cpp\llama-server.exe",
        "$env:USERPROFILE\llama.cpp\build\bin\Release\llama-server.exe",
        "$env:USERPROFILE\llama.cpp\llama-server.exe"
    )
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            return @{ Installed = $true; Path = $path; Source = "System" }
        }
    }
    
    return @{ Installed = $false; Path = $null; Source = $null }
}

function Test-PythonPackageInstalled {
    param([string]$Package)
    
    # First check venv if it exists
    $venvPython = Join-Path $ProjectRoot "server\.venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        try {
            $result = & $venvPython -c "import $Package; print('installed')" 2>&1
            if ($result -eq "installed") {
                return @{ Installed = $true; Source = "venv" }
            }
        } catch {}
    }
    
    # Check system Python
    try {
        $result = python -c "import $Package; print('installed')" 2>&1
        if ($result -eq "installed") {
            return @{ Installed = $true; Source = "system" }
        }
    } catch {}
    
    return @{ Installed = $false; Source = $null }
}

function Get-InstalledStatus {
    $status = @{
        LlamaCpp = Test-LlamaCppInstalled
        HuggingFace = Test-PythonPackageInstalled "huggingface_hub"
        LiteLLM = Test-PythonPackageInstalled "litellm"
        GPU = Test-PythonPackageInstalled "GPUtil"
    }
    
    return $status
}
#endregion

#region Prerequisites Check
Write-Host "Checking prerequisites..." -ForegroundColor Cyan

# Check for Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Error: Python is required but not installed." -ForegroundColor Red
    Write-Host "Install Python 3.10+ from https://python.org"
    exit 1
}
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "  Python: $pythonVersion" -ForegroundColor Green

# Check for Node.js
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "Error: Node.js is required but not installed." -ForegroundColor Red
    Write-Host "Install Node.js 18+ from https://nodejs.org"
    exit 1
}
$nodeVersion = node --version
Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green

# Check for npm
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    Write-Host "Error: npm is required but not installed." -ForegroundColor Red
    exit 1
}
$npmVersion = npm --version
Write-Host "  npm: $npmVersion" -ForegroundColor Green

# Check for Rust/Cargo (optional)
$TauriAvailable = $false
if (-not $SkipTauri) {
    $cargo = Get-Command cargo -ErrorAction SilentlyContinue
    if ($cargo) {
        $cargoVersion = (cargo --version) -replace 'cargo ', ''
        Write-Host "  Rust/Cargo: $cargoVersion" -ForegroundColor Green
        $TauriAvailable = $true
    } else {
        Write-Host "  Rust/Cargo: Not installed (optional)" -ForegroundColor Yellow
    }
}

Write-Host ""
#endregion

#region Detect Already Installed Components
Write-Host "Detecting installed components..." -ForegroundColor Cyan
$installed = Get-InstalledStatus

# llama.cpp
if ($installed.LlamaCpp.Installed) {
    Write-Host "  llama.cpp: " -NoNewline -ForegroundColor White
    Write-Host "Installed" -NoNewline -ForegroundColor Green
    Write-Host " ($($installed.LlamaCpp.Source): $($installed.LlamaCpp.Path))" -ForegroundColor Gray
} else {
    Write-Host "  llama.cpp: " -NoNewline -ForegroundColor White
    Write-Host "Not installed" -ForegroundColor Yellow
}

# Hugging Face
if ($installed.HuggingFace.Installed) {
    Write-Host "  Hugging Face Hub: " -NoNewline -ForegroundColor White
    Write-Host "Installed" -NoNewline -ForegroundColor Green
    Write-Host " ($($installed.HuggingFace.Source))" -ForegroundColor Gray
} else {
    Write-Host "  Hugging Face Hub: " -NoNewline -ForegroundColor White
    Write-Host "Not installed" -ForegroundColor Yellow
}

# LiteLLM
if ($installed.LiteLLM.Installed) {
    Write-Host "  LiteLLM: " -NoNewline -ForegroundColor White
    Write-Host "Installed" -NoNewline -ForegroundColor Green
    Write-Host " ($($installed.LiteLLM.Source))" -ForegroundColor Gray
} else {
    Write-Host "  LiteLLM: " -NoNewline -ForegroundColor White
    Write-Host "Not installed" -ForegroundColor Yellow
}

# GPU
if ($installed.GPU.Installed) {
    Write-Host "  GPU support: " -NoNewline -ForegroundColor White
    Write-Host "Installed" -NoNewline -ForegroundColor Green
    Write-Host " ($($installed.GPU.Source))" -ForegroundColor Gray
} else {
    Write-Host "  GPU support: " -NoNewline -ForegroundColor White
    Write-Host "Not installed" -ForegroundColor Yellow
}

Write-Host ""
#endregion

#region Optional Components Selection
$InstallLlamaCpp = $false
$InstallLiteLLM = $false
$InstallHuggingFace = $false
$InstallGPU = $false

if ($All) {
    # Install all, but skip already installed
    $InstallLlamaCpp = -not $installed.LlamaCpp.Installed
    $InstallLiteLLM = -not $installed.LiteLLM.Installed
    $InstallHuggingFace = -not $installed.HuggingFace.Installed
    $InstallGPU = -not $installed.GPU.Installed
} elseif ($Minimal) {
    # All false by default
} elseif (-not $NoPrompt) {
    Write-Host "Optional Components" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Host "(Press Enter for default, or type y/n)" -ForegroundColor Gray
    Write-Host ""
    
    # llama.cpp
    if ($installed.LlamaCpp.Installed) {
        Write-Host "llama.cpp - Local inference engine" -ForegroundColor White
        Write-Host "  Already installed at: $($installed.LlamaCpp.Path)" -ForegroundColor Green
        $InstallLlamaCpp = $false
    } else {
        Write-Host "llama.cpp - Local inference engine" -ForegroundColor White
        Write-Host "  Required to run models locally on your machine" -ForegroundColor Gray
        $response = Read-Host "  Show installation instructions? [Y/n]"
        if ($response -eq "" -or $response -match "^[Yy]") {
            $InstallLlamaCpp = $true
        }
    }
    Write-Host ""
    
    # Hugging Face Hub
    if ($installed.HuggingFace.Installed) {
        Write-Host "Hugging Face Hub - Model downloads" -ForegroundColor White
        Write-Host "  Already installed ($($installed.HuggingFace.Source))" -ForegroundColor Green
        $InstallHuggingFace = $false
    } else {
        Write-Host "Hugging Face Hub - Model downloads" -ForegroundColor White
        Write-Host "  Required to download models from Hugging Face" -ForegroundColor Gray
        $response = Read-Host "  Install Hugging Face Hub? [Y/n]"
        if ($response -eq "" -or $response -match "^[Yy]") {
            $InstallHuggingFace = $true
        }
    }
    Write-Host ""
    
    # LiteLLM
    if ($installed.LiteLLM.Installed) {
        Write-Host "LiteLLM - Cloud model routing" -ForegroundColor White
        Write-Host "  Already installed ($($installed.LiteLLM.Source))" -ForegroundColor Green
        $InstallLiteLLM = $false
    } else {
        Write-Host "LiteLLM - Cloud model routing" -ForegroundColor White
        Write-Host "  Required for OpenAI, Anthropic, and other cloud APIs" -ForegroundColor Gray
        $response = Read-Host "  Install LiteLLM? [y/N]"
        if ($response -match "^[Yy]") {
            $InstallLiteLLM = $true
        }
    }
    Write-Host ""
    
    # GPU support
    if ($installed.GPU.Installed) {
        Write-Host "GPU Support - NVIDIA GPU detection" -ForegroundColor White
        Write-Host "  Already installed ($($installed.GPU.Source))" -ForegroundColor Green
        $InstallGPU = $false
    } else {
        Write-Host "GPU Support - NVIDIA GPU detection" -ForegroundColor White
        Write-Host "  Enables automatic GPU layer offloading" -ForegroundColor Gray
        $response = Read-Host "  Install GPU support? [Y/n]"
        if ($response -eq "" -or $response -match "^[Yy]") {
            $InstallGPU = $true
        }
    }
    Write-Host ""
} else {
    Write-Host "No optional components selected (use -All or interactive mode)" -ForegroundColor Yellow
    Write-Host ""
}

# Show selection summary
$anyToInstall = $InstallLlamaCpp -or $InstallHuggingFace -or $InstallLiteLLM -or $InstallGPU
if ($anyToInstall) {
    Write-Host "Components to install:" -ForegroundColor Cyan
    if ($InstallLlamaCpp) { Write-Host "  + llama.cpp" -ForegroundColor Green }
    if ($InstallHuggingFace) { Write-Host "  + Hugging Face Hub" -ForegroundColor Green }
    if ($InstallLiteLLM) { Write-Host "  + LiteLLM" -ForegroundColor Green }
    if ($InstallGPU) { Write-Host "  + GPU support" -ForegroundColor Green }
    Write-Host ""
}
#endregion

#region Create Directories
Write-Host "Creating data directories..." -ForegroundColor Cyan
$null = New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "models")
$null = New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "data")
$null = New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "logs")
$null = New-Item -ItemType Directory -Force -Path $BinDir
Write-Host "  Created: $DataDir" -ForegroundColor Green
Write-Host ""
#endregion

#region Install llama.cpp
function Show-LlamaCppInstructions {
    Write-Host "llama.cpp Installation Instructions" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "llama.cpp is required to run models locally." -ForegroundColor White
    Write-Host ""
    Write-Host "Install using one of these methods:" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 1: Winget (Recommended)" -ForegroundColor Green
    Write-Host "  winget install llama.cpp" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 2: Download from GitHub" -ForegroundColor Green
    Write-Host "  https://github.com/ggml-org/llama.cpp/releases" -ForegroundColor Gray
    Write-Host "  Download the Windows binary and add to PATH" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 3: Build from source" -ForegroundColor Green
    Write-Host "  git clone https://github.com/ggml-org/llama.cpp" -ForegroundColor Gray
    Write-Host "  cd llama.cpp && cmake -B build && cmake --build build --config Release" -ForegroundColor Gray
    Write-Host ""
    Write-Host "After installation, ensure 'llama-server' is in your PATH." -ForegroundColor Yellow
    Write-Host ""
}
    
    # Get latest release from GitHub
    $releaseUrl = "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
    try {
        $release = Invoke-RestMethod -Uri $releaseUrl -Headers @{ "User-Agent" = "LLMLaunchpad" }
        $version = $release.tag_name
        Write-Host "  Latest version: $version" -ForegroundColor Gray
        
        # Find appropriate asset
        $asset = $null
        
        if ($hasCuda) {
            # Prefer CUDA build
            $asset = $release.assets | Where-Object { 
                $_.name -match "cudart.*win.*x64.*\.zip$" -or 
                $_.name -match "win.*cuda.*x64.*\.zip$" 
            } | Select-Object -First 1
        }
        
        if (-not $asset) {
            # Fall back to CPU build (AVX2 preferred)
            $asset = $release.assets | Where-Object { 
                $_.name -match "win.*x64.*\.zip$" -and $_.name -notmatch "cuda"
            } | Select-Object -First 1
        }
        
        if (-not $asset) {
            # Try any Windows zip
            $asset = $release.assets | Where-Object { 
                $_.name -match "win.*\.zip$"
            } | Select-Object -First 1
        }
        
        if ($asset) {
            $downloadUrl = $asset.browser_download_url
            $zipPath = Join-Path $env:TEMP "llama-cpp.zip"
            $extractPath = Join-Path $env:TEMP "llama-cpp-extract"
            
            Write-Host "  Downloading: $($asset.name)" -ForegroundColor Gray
            Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
            
            Write-Host "  Extracting..." -ForegroundColor Gray
            if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }
            Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
            
            # Find and copy llama-server executable
            $serverExe = Get-ChildItem -Path $extractPath -Recurse -Filter "llama-server.exe" | Select-Object -First 1
            if ($serverExe) {
                Copy-Item -Path $serverExe.FullName -Destination (Join-Path $BinDir "llama-server.exe") -Force
                Write-Host "  Installed: llama-server.exe" -ForegroundColor Green
                
                # Copy any DLLs in the same directory
                $dllFiles = Get-ChildItem -Path $serverExe.DirectoryName -Filter "*.dll"
                foreach ($dll in $dllFiles) {
                    Copy-Item -Path $dll.FullName -Destination $BinDir -Force
                    Write-Host "  Copied: $($dll.Name)" -ForegroundColor Gray
                }
            } else {
                Write-Host "  Warning: llama-server.exe not found in release" -ForegroundColor Yellow
                Write-Host "  Download manually from: https://github.com/ggerganov/llama.cpp/releases" -ForegroundColor Yellow
            }
            
            # Cleanup
            Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $extractPath -Recurse -Force -ErrorAction SilentlyContinue
        } else {
            Write-Host "  Error: No suitable Windows release found" -ForegroundColor Red
            Write-Host "  Download manually from: https://github.com/ggerganov/llama.cpp/releases" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Error downloading llama.cpp: $_" -ForegroundColor Red
        Write-Host "  Download manually from: https://github.com/ggerganov/llama.cpp/releases" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($InstallLlamaCpp) {
    Install-LlamaCpp
}
#endregion

#region Install Node Dependencies
Write-Host "Installing root dependencies..." -ForegroundColor Cyan
npm install --silent
Write-Host ""
#endregion

#region Install Python Backend
Write-Host "Setting up Python backend..." -ForegroundColor Cyan
Push-Location server

# Check if any packages are installed globally
$useSystemPackages = $installed.HuggingFace.Source -eq "system" -or 
                     $installed.LiteLLM.Source -eq "system" -or 
                     $installed.GPU.Source -eq "system"

if (-not (Test-Path ".venv")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    if ($useSystemPackages) {
        Write-Host "  Using system-site-packages (global packages detected)" -ForegroundColor Gray
        python -m venv .venv --system-site-packages
    } else {
        python -m venv .venv
    }
}
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip --quiet

# Build pip extras string - only install what's NOT already in system
$extras = @()
if ($InstallHuggingFace) { $extras += "hf" }
if ($InstallLiteLLM) { $extras += "cloud" }
if ($InstallGPU) { $extras += "gpu" }

if ($extras.Count -gt 0) {
    $extrasStr = $extras -join ","
    Write-Host "  Installing with extras: [$extrasStr]" -ForegroundColor Gray
    pip install -e ".[$extrasStr]" --quiet
} else {
    Write-Host "  Installing core only" -ForegroundColor Gray
    pip install -e . --quiet
}

deactivate
Pop-Location
Write-Host "  Backend installed" -ForegroundColor Green
Write-Host ""
#endregion

#region Install Frontend
Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location app
npm install --silent
Pop-Location
Write-Host "  Frontend installed" -ForegroundColor Green
Write-Host ""
#endregion

#region Summary
Write-Host "==========================================" -ForegroundColor White
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor White
Write-Host ""

# Refresh installed status
$finalStatus = Get-InstalledStatus

Write-Host "Installed components:" -ForegroundColor Cyan
Write-Host "  Core (FastAPI, Svelte UI)" -ForegroundColor Green

# llama.cpp status
if ($finalStatus.LlamaCpp.Installed) {
    Write-Host "  llama.cpp: $($finalStatus.LlamaCpp.Path)" -ForegroundColor Green
} else {
    Write-Host "  llama.cpp: Not installed" -ForegroundColor Yellow
}

# Python packages
if ($finalStatus.HuggingFace.Installed) { 
    Write-Host "  Hugging Face Hub ($($finalStatus.HuggingFace.Source))" -ForegroundColor Green 
}
if ($finalStatus.LiteLLM.Installed) { 
    Write-Host "  LiteLLM ($($finalStatus.LiteLLM.Source))" -ForegroundColor Green 
}
if ($finalStatus.GPU.Installed) { 
    Write-Host "  GPU support ($($finalStatus.GPU.Source))" -ForegroundColor Green 
}

Write-Host ""

Write-Host "To start development:" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor Cyan -NoNewline
Write-Host "          - Web app + backend"
if ($TauriAvailable) {
    Write-Host "  npm run dev:tauri" -ForegroundColor Cyan -NoNewline
    Write-Host "    - Desktop app + backend"
}
Write-Host ""
Write-Host "Open in browser: http://localhost:5173"
Write-Host ""

# Add bin directory to PATH hint if llama.cpp was installed there
if ($finalStatus.LlamaCpp.Installed -and $finalStatus.LlamaCpp.Source -eq "LLMLaunchpad") {
    Write-Host "Tip: Add llama.cpp to your PATH:" -ForegroundColor Yellow
    Write-Host "  `$env:PATH += `";$BinDir`"" -ForegroundColor Gray
    Write-Host ""
}
#endregion
