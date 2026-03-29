#!/bin/bash
# LLMLaunchpad - Install Script (Unix/macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Data directories
DATA_DIR="$HOME/.llmlaunchpad"
BIN_DIR="$DATA_DIR/bin"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_TAURI=false
ALL=false
MINIMAL=false
NO_PROMPT=false

for arg in "$@"; do
    case $arg in
        --skip-tauri)
            SKIP_TAURI=true
            ;;
        --all)
            ALL=true
            ;;
        --minimal)
            MINIMAL=true
            ;;
        --no-prompt)
            NO_PROMPT=true
            ;;
        --help|-h)
            echo "Usage: install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all          Install all optional components"
            echo "  --minimal      Install only core (skip all optional)"
            echo "  --no-prompt    Non-interactive mode (use --all or --minimal)"
            echo "  --skip-tauri   Skip Rust/Tauri check"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Optional components:"
            echo "  - llama.cpp     Local inference engine (downloads binary)"
            echo "  - LiteLLM       Cloud model routing (OpenAI, Anthropic, etc.)"
            echo "  - Hugging Face  Model downloads from HF Hub"
            echo "  - GPU support   NVIDIA GPU detection"
            exit 0
            ;;
    esac
done

echo -e "${WHITE}==========================================${NC}"
echo -e "${CYAN}  LLMLaunchpad Installer${NC}"
echo -e "${WHITE}==========================================${NC}"
echo ""

#region Detection Functions
detect_llama_cpp() {
    # Check in our bin directory
    if [ -f "$BIN_DIR/llama-server" ]; then
        echo "LLMLaunchpad:$BIN_DIR/llama-server"
        return 0
    fi
    
    # Check in PATH
    if command -v llama-server &> /dev/null; then
        echo "PATH:$(which llama-server)"
        return 0
    fi
    
    # Check common locations
    local common_paths=(
        "/usr/local/bin/llama-server"
        "$HOME/.local/bin/llama-server"
        "$HOME/llama.cpp/build/bin/llama-server"
    )
    for path in "${common_paths[@]}"; do
        if [ -f "$path" ]; then
            echo "System:$path"
            return 0
        fi
    done
    
    return 1
}

check_python_package() {
    local package=$1
    
    # First check venv if it exists
    local venv_python="$PROJECT_ROOT/server/.venv/bin/python"
    if [ -f "$venv_python" ]; then
        if $venv_python -c "import $package" 2>/dev/null; then
            echo "venv"
            return 0
        fi
    fi
    
    # Check system Python
    if python3 -c "import $package" 2>/dev/null; then
        echo "system"
        return 0
    fi
    
    return 1
}

detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux" ;;
        Darwin*)    echo "macos" ;;
        *)          echo "unknown" ;;
    esac
}

detect_arch() {
    case "$(uname -m)" in
        x86_64)     echo "x64" ;;
        aarch64)    echo "arm64" ;;
        arm64)      echo "arm64" ;;
        *)          echo "unknown" ;;
    esac
}
#endregion

#region Prerequisites Check
echo -e "${CYAN}Checking prerequisites...${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    echo "Install Python 3.10+ from https://python.org"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  Python: ${GREEN}$PYTHON_VERSION${NC}"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required but not installed.${NC}"
    echo "Install Node.js 18+ from https://nodejs.org"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "  Node.js: ${GREEN}$NODE_VERSION${NC}"

# Check for npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is required but not installed.${NC}"
    exit 1
fi
NPM_VERSION=$(npm --version)
echo -e "  npm: ${GREEN}$NPM_VERSION${NC}"

# Check for Rust/Cargo (optional)
TAURI_AVAILABLE=false
if [ "$SKIP_TAURI" = false ]; then
    if command -v cargo &> /dev/null; then
        CARGO_VERSION=$(cargo --version | cut -d' ' -f2)
        echo -e "  Rust/Cargo: ${GREEN}$CARGO_VERSION${NC}"
        TAURI_AVAILABLE=true
    else
        echo -e "  Rust/Cargo: ${YELLOW}Not installed (optional)${NC}"
    fi
fi

echo ""
#endregion

#region Detect Already Installed Components
echo -e "${CYAN}Detecting installed components...${NC}"

# llama.cpp
LLAMA_INSTALLED=""
if LLAMA_RESULT=$(detect_llama_cpp); then
    LLAMA_INSTALLED="$LLAMA_RESULT"
    LLAMA_SOURCE="${LLAMA_INSTALLED%%:*}"
    LLAMA_PATH="${LLAMA_INSTALLED#*:}"
    echo -e "  llama.cpp: ${GREEN}Installed${NC} ${GRAY}($LLAMA_SOURCE: $LLAMA_PATH)${NC}"
else
    echo -e "  llama.cpp: ${YELLOW}Not installed${NC}"
fi

# Hugging Face
HF_INSTALLED=""
if HF_SOURCE=$(check_python_package "huggingface_hub"); then
    HF_INSTALLED="$HF_SOURCE"
    echo -e "  Hugging Face Hub: ${GREEN}Installed${NC} ${GRAY}($HF_SOURCE)${NC}"
else
    echo -e "  Hugging Face Hub: ${YELLOW}Not installed${NC}"
fi

# LiteLLM
LITELLM_INSTALLED=""
if LITELLM_SOURCE=$(check_python_package "litellm"); then
    LITELLM_INSTALLED="$LITELLM_SOURCE"
    echo -e "  LiteLLM: ${GREEN}Installed${NC} ${GRAY}($LITELLM_SOURCE)${NC}"
else
    echo -e "  LiteLLM: ${YELLOW}Not installed${NC}"
fi

# GPU
GPU_INSTALLED=""
if GPU_SOURCE=$(check_python_package "GPUtil"); then
    GPU_INSTALLED="$GPU_SOURCE"
    echo -e "  GPU support: ${GREEN}Installed${NC} ${GRAY}($GPU_SOURCE)${NC}"
else
    echo -e "  GPU support: ${YELLOW}Not installed${NC}"
fi

echo ""
#endregion

#region Optional Components Selection
INSTALL_LLAMA=false
INSTALL_HF=false
INSTALL_LITELLM=false
INSTALL_GPU=false

if [ "$ALL" = true ]; then
    # Install all, but skip already installed
    [ -z "$LLAMA_INSTALLED" ] && INSTALL_LLAMA=true
    [ -z "$HF_INSTALLED" ] && INSTALL_HF=true
    [ -z "$LITELLM_INSTALLED" ] && INSTALL_LITELLM=true
    [ -z "$GPU_INSTALLED" ] && INSTALL_GPU=true
elif [ "$MINIMAL" = true ]; then
    # All false by default
    :
elif [ "$NO_PROMPT" = false ]; then
    echo -e "${CYAN}Optional Components${NC}"
    echo -e "${CYAN}===================${NC}"
    echo -e "${GRAY}(Press Enter for default, or type y/n)${NC}"
    echo ""
    
    # llama.cpp
    if [ -n "$LLAMA_INSTALLED" ]; then
        echo -e "${WHITE}llama.cpp - Local inference engine${NC}"
        echo -e "  ${GREEN}Already installed at: $LLAMA_PATH${NC}"
    else
        echo -e "${WHITE}llama.cpp - Local inference engine${NC}"
        echo -e "  ${GRAY}Required to run models locally on your machine${NC}"
        read -p "  Install llama.cpp? [Y/n] " response
        if [[ "$response" == "" || "$response" =~ ^[Yy] ]]; then
            INSTALL_LLAMA=true
        fi
    fi
    echo ""
    
    # Hugging Face Hub
    if [ -n "$HF_INSTALLED" ]; then
        echo -e "${WHITE}Hugging Face Hub - Model downloads${NC}"
        echo -e "  ${GREEN}Already installed ($HF_INSTALLED)${NC}"
    else
        echo -e "${WHITE}Hugging Face Hub - Model downloads${NC}"
        echo -e "  ${GRAY}Required to download models from Hugging Face${NC}"
        read -p "  Install Hugging Face Hub? [Y/n] " response
        if [[ "$response" == "" || "$response" =~ ^[Yy] ]]; then
            INSTALL_HF=true
        fi
    fi
    echo ""
    
    # LiteLLM
    if [ -n "$LITELLM_INSTALLED" ]; then
        echo -e "${WHITE}LiteLLM - Cloud model routing${NC}"
        echo -e "  ${GREEN}Already installed ($LITELLM_INSTALLED)${NC}"
    else
        echo -e "${WHITE}LiteLLM - Cloud model routing${NC}"
        echo -e "  ${GRAY}Required for OpenAI, Anthropic, and other cloud APIs${NC}"
        read -p "  Install LiteLLM? [y/N] " response
        if [[ "$response" =~ ^[Yy] ]]; then
            INSTALL_LITELLM=true
        fi
    fi
    echo ""
    
     # GPU support
     if [ -n "$GPU_INSTALLED" ]; then
         echo -e "${WHITE}GPU Support - NVIDIA GPU detection${NC}"
         echo -e "  ${GREEN}Already installed ($GPU_INSTALLED)${NC}"
     else
         echo -e "${WHITE}GPU Support - NVIDIA GPU detection${NC}"
         echo -e "  ${GRAY}Enables automatic GPU layer offloading${NC}"
         read -p "  Install GPU support? [Y/n] " response
         if [[ "$response" == "" || "$response" =~ ^[Yy] ]]; then
             INSTALL_GPU=true
         fi
     fi
     
     echo ""
    
    # LiteLLM
    if [ "$LITELLM_INSTALLED" = true ]; then
        echo -e "${WHITE}LiteLLM - Cloud model routing${NC}"
        echo -e "  ${GREEN}Already installed${NC}"
    else
        echo -e "${WHITE}LiteLLM - Cloud model routing${NC}"
        echo -e "  ${GRAY}Required for OpenAI, Anthropic, and other cloud APIs${NC}"
        read -p "  Install LiteLLM? [y/N] " response
        if [[ "$response" =~ ^[Yy] ]]; then
            INSTALL_LITELLM=true
        fi
    fi
    echo ""
    
    # GPU support
    if [ "$GPU_INSTALLED" = true ]; then
        echo -e "${WHITE}GPU Support - NVIDIA GPU detection${NC}"
        echo -e "  ${GREEN}Already installed${NC}"
    else
        echo -e "${WHITE}GPU Support - NVIDIA GPU detection${NC}"
        echo -e "  ${GRAY}Enables automatic GPU layer offloading${NC}"
        read -p "  Install GPU support? [Y/n] " response
        if [[ "$response" == "" || "$response" =~ ^[Yy] ]]; then
            INSTALL_GPU=true
        fi
    fi
    echo ""
else
    echo -e "${YELLOW}No optional components selected (use --all or interactive mode)${NC}"
    echo ""
fi

# Show selection summary
if [ "$INSTALL_LLAMA" = true ] || [ "$INSTALL_HF" = true ] || [ "$INSTALL_LITELLM" = true ] || [ "$INSTALL_GPU" = true ]; then
    echo -e "${CYAN}Components to install:${NC}"
    [ "$INSTALL_LLAMA" = true ] && echo -e "  ${GREEN}+ llama.cpp${NC}"
    [ "$INSTALL_HF" = true ] && echo -e "  ${GREEN}+ Hugging Face Hub${NC}"
    [ "$INSTALL_LITELLM" = true ] && echo -e "  ${GREEN}+ LiteLLM${NC}"
    [ "$INSTALL_GPU" = true ] && echo -e "  ${GREEN}+ GPU support${NC}"
    echo ""
fi
#endregion

#region Create Directories
echo -e "${CYAN}Creating data directories...${NC}"
mkdir -p "$DATA_DIR/models"
mkdir -p "$DATA_DIR/data"
mkdir -p "$DATA_DIR/logs"
mkdir -p "$BIN_DIR"
echo -e "  Created: ${GREEN}$DATA_DIR${NC}"
echo ""
#endregion

#region Install llama.cpp
install_llama_cpp() {
    echo -e "${CYAN}Installing llama.cpp...${NC}"
    
    local os=$(detect_os)
    local arch=$(detect_arch)
    
    echo -e "  ${GRAY}Detected: $os ($arch)${NC}"
    
    # Check for CUDA on Linux
    local has_cuda=false
    if command -v nvcc &> /dev/null; then
        has_cuda=true
        echo -e "  ${GRAY}CUDA detected, preferring CUDA build${NC}"
    fi
    
    # Get latest release from GitHub
    local release_url="https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
    local release_json
    
    if command -v curl &> /dev/null; then
        release_json=$(curl -s -H "User-Agent: LLMLaunchpad" "$release_url")
    elif command -v wget &> /dev/null; then
        release_json=$(wget -q -O - --header="User-Agent: LLMLaunchpad" "$release_url")
    else
        echo -e "  ${RED}Error: curl or wget required${NC}"
        return 1
    fi
    
    local version=$(echo "$release_json" | grep -o '"tag_name": *"[^"]*"' | head -1 | cut -d'"' -f4)
    echo -e "  ${GRAY}Latest version: $version${NC}"
    
    # Find appropriate asset based on OS
    local asset_pattern=""
    case "$os" in
        macos)
            if [ "$arch" = "arm64" ]; then
                asset_pattern="macos-arm64"
            else
                asset_pattern="macos-x64"
            fi
            ;;
        linux)
            if [ "$has_cuda" = true ]; then
                asset_pattern="linux.*cuda.*$arch"
            else
                asset_pattern="linux.*$arch"
            fi
            ;;
    esac
    
    # Extract download URL
    local download_url=$(echo "$release_json" | grep -o '"browser_download_url": *"[^"]*'"$asset_pattern"'[^"]*\.zip"' | head -1 | cut -d'"' -f4)
    
    if [ -z "$download_url" ]; then
        # Fallback: try without CUDA
        download_url=$(echo "$release_json" | grep -o '"browser_download_url": *"[^"]*'"$os"'[^"]*\.zip"' | grep -v cuda | head -1 | cut -d'"' -f4)
    fi
    
    if [ -n "$download_url" ]; then
        local zip_path="/tmp/llama-cpp.zip"
        local extract_path="/tmp/llama-cpp-extract"
        
        local asset_name=$(basename "$download_url")
        echo -e "  ${GRAY}Downloading: $asset_name${NC}"
        
        if command -v curl &> /dev/null; then
            curl -L -o "$zip_path" "$download_url"
        else
            wget -O "$zip_path" "$download_url"
        fi
        
        echo -e "  ${GRAY}Extracting...${NC}"
        rm -rf "$extract_path"
        unzip -q "$zip_path" -d "$extract_path"
        
        # Find and copy llama-server
        local server_bin=$(find "$extract_path" -name "llama-server" -type f | head -1)
        if [ -n "$server_bin" ]; then
            cp "$server_bin" "$BIN_DIR/llama-server"
            chmod +x "$BIN_DIR/llama-server"
            echo -e "  ${GREEN}Installed: llama-server${NC}"
            
            # Copy any .so/.dylib files
            local lib_dir=$(dirname "$server_bin")
            find "$lib_dir" -name "*.so*" -o -name "*.dylib" 2>/dev/null | while read lib; do
                cp "$lib" "$BIN_DIR/"
                echo -e "  ${GRAY}Copied: $(basename "$lib")${NC}"
            done
        else
            echo -e "  ${YELLOW}Warning: llama-server not found in release${NC}"
        fi
        
        # Cleanup
        rm -f "$zip_path"
        rm -rf "$extract_path"
    else
        echo -e "  ${RED}Error: No suitable release found for $os ($arch)${NC}"
        echo -e "  ${YELLOW}Download manually from: https://github.com/ggerganov/llama.cpp/releases${NC}"
    fi
    
    echo ""
}

if [ "$INSTALL_LLAMA" = true ]; then
    install_llama_cpp
fi
#endregion

#region Install Node Dependencies
echo -e "${CYAN}Installing root dependencies...${NC}"
npm install --silent
echo ""
#endregion

#region Install Python Backend
echo -e "${CYAN}Setting up Python backend...${NC}"
cd server

# Check if any packages are installed globally
USE_SYSTEM_PACKAGES=false
if [ "$HF_INSTALLED" = "system" ] || [ "$LITELLM_INSTALLED" = "system" ] || [ "$GPU_INSTALLED" = "system" ]; then
    USE_SYSTEM_PACKAGES=true
fi

if [ ! -d ".venv" ]; then
    echo -e "  ${GRAY}Creating virtual environment...${NC}"
    if [ "$USE_SYSTEM_PACKAGES" = true ]; then
        echo -e "  ${GRAY}Using system-site-packages (global packages detected)${NC}"
        python3 -m venv .venv --system-site-packages
    else
        python3 -m venv .venv
    fi
fi

source .venv/bin/activate
pip install --upgrade pip --quiet

# Build pip extras string - only install what's NOT already in system
extras=""
if [ "$INSTALL_HF" = true ]; then
    extras="${extras}hf,"
fi
if [ "$INSTALL_LITELLM" = true ]; then
    extras="${extras}cloud,"
fi
if [ "$INSTALL_GPU" = true ]; then
    extras="${extras}gpu,"
fi

# Remove trailing comma
extras="${extras%,}"

if [ -n "$extras" ]; then
    echo -e "  ${GRAY}Installing with extras: [$extras]${NC}"
    pip install -e ".[$extras]" --quiet
else
    echo -e "  ${GRAY}Installing core only${NC}"
    pip install -e . --quiet
fi

deactivate
cd ..
echo -e "  ${GREEN}Backend installed${NC}"
echo ""
#endregion

#region Install Frontend
echo -e "${CYAN}Installing frontend dependencies...${NC}"
cd app
npm install --silent
cd ..
echo -e "  ${GREEN}Frontend installed${NC}"
echo ""
#endregion

#region Summary
echo -e "${WHITE}==========================================${NC}"
echo -e "${GREEN}Installation complete!${NC}"
echo -e "${WHITE}==========================================${NC}"
echo ""

# Show final status
echo -e "${CYAN}Installed components:${NC}"
echo -e "  ${GREEN}Core (FastAPI, Svelte UI)${NC}"

# Check llama.cpp again
if LLAMA_RESULT=$(detect_llama_cpp); then
    LLAMA_PATH="${LLAMA_RESULT#*:}"
    echo -e "  ${GREEN}llama.cpp: $LLAMA_PATH${NC}"
else
    echo -e "  ${YELLOW}llama.cpp: Not installed${NC}"
fi

# Python packages (re-check to show source)
if HF_SRC=$(check_python_package "huggingface_hub"); then
    echo -e "  ${GREEN}Hugging Face Hub ($HF_SRC)${NC}"
fi
if LITELLM_SRC=$(check_python_package "litellm"); then
    echo -e "  ${GREEN}LiteLLM ($LITELLM_SRC)${NC}"
fi
if GPU_SRC=$(check_python_package "GPUtil"); then
    echo -e "  ${GREEN}GPU support ($GPU_SRC)${NC}"
fi

echo ""

echo -e "To start development:"
echo -e "  ${CYAN}npm run dev${NC}          - Web app + backend"
if [ "$TAURI_AVAILABLE" = true ]; then
    echo -e "  ${CYAN}npm run dev:tauri${NC}    - Desktop app + backend"
fi
echo ""
echo "Open in browser: http://localhost:5173"
echo ""

# Add bin directory to PATH hint
if [ -f "$BIN_DIR/llama-server" ]; then
    echo -e "${YELLOW}Tip: Add llama.cpp to your PATH:${NC}"
    echo -e "  ${GRAY}export PATH=\"\$PATH:$BIN_DIR\"${NC}"
    echo ""
fi
#endregion
