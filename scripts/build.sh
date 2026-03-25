#!/bin/bash
# LLMLaunchpad - Build Script (Unix/macOS)

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
        --all)
            MODE="all"
            shift
            ;;
        --help|-h)
            echo "Usage: build.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --tauri       Build Tauri desktop app only"
            echo "  --all         Build both web and Tauri"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Default: Builds web app only (app/dist/)"
            exit 0
            ;;
    esac
done

echo -e "${CYAN}=========================================="
echo -e "  LLMLaunchpad Build"
echo -e "==========================================${NC}"
echo ""

# Check if dependencies are installed
if [ ! -d "app/node_modules" ]; then
    echo -e "${RED}Error: Frontend not installed.${NC}"
    echo "Run ./scripts/install.sh first."
    exit 1
fi

# Build web
build_web() {
    echo -e "${CYAN}Building web app...${NC}"
    cd app
    npm run build
    cd ..
    echo -e "${GREEN}Web build complete: app/dist/${NC}"
}

# Build Tauri
build_tauri() {
    # Check for Rust
    if ! command -v cargo &> /dev/null; then
        echo -e "${RED}Error: Rust/Cargo is required for Tauri build.${NC}"
        echo "Install from https://rustup.rs"
        exit 1
    fi
    
    echo -e "${CYAN}Building Tauri desktop app...${NC}"
    cd app
    npm run tauri:build
    cd ..
    echo -e "${GREEN}Tauri build complete: app/src-tauri/target/release/${NC}"
    
    # Show output files
    echo ""
    echo -e "${CYAN}Build artifacts:${NC}"
    if [ -d "app/src-tauri/target/release/bundle" ]; then
        find app/src-tauri/target/release/bundle -type f \( -name "*.dmg" -o -name "*.app" -o -name "*.AppImage" -o -name "*.deb" -o -name "*.exe" -o -name "*.msi" \) 2>/dev/null | while read file; do
            size=$(du -h "$file" | cut -f1)
            echo -e "  ${GREEN}$file${NC} ($size)"
        done
    fi
}

case $MODE in
    web)
        build_web
        ;;
    tauri)
        build_tauri
        ;;
    all)
        build_web
        echo ""
        build_tauri
        ;;
esac

echo ""
echo -e "${GREEN}Build complete!${NC}"
