#!/bin/bash
# LLMLaunchpad - Development Script (Unix/macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
MODE="web"
for arg in "$@"; do
    case $arg in
        --tauri)
            MODE="tauri"
            shift
            ;;
        --help|-h)
            echo "Usage: dev.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --tauri       Run Tauri desktop app instead of web"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Default: Runs web app + backend"
            exit 0
            ;;
    esac
done

# Check if dependencies are installed
if [ ! -d "server/.venv" ]; then
    echo -e "${RED}Error: Backend not installed.${NC}"
    echo "Run ./scripts/install.sh first."
    exit 1
fi

if [ ! -d "app/node_modules" ]; then
    echo -e "${RED}Error: Frontend not installed.${NC}"
    echo "Run ./scripts/install.sh first."
    exit 1
fi

# Start servers
if [ "$MODE" = "tauri" ]; then
    # Check for Rust
    if ! command -v cargo &> /dev/null; then
        echo -e "${RED}Error: Rust/Cargo is required for Tauri mode.${NC}"
        echo "Install from https://rustup.rs"
        exit 1
    fi
    
    echo -e "${CYAN}Starting LLMLaunchpad (Tauri desktop + backend)...${NC}"
    echo ""
    npm run dev:tauri
else
    echo -e "${CYAN}Starting LLMLaunchpad (web + backend)...${NC}"
    echo ""
    echo -e "Web UI: ${GREEN}http://localhost:5173${NC}"
    echo -e "API:    ${GREEN}http://localhost:8000${NC}"
    echo ""
    npm run dev
fi
