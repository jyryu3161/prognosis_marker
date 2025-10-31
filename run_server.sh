#!/bin/bash

# ============================================================================
# Prognosis Marker - Streamlit Server Launch Script
# ============================================================================
# This script launches the Streamlit codebase analyzer web interface.
# Dependencies must be installed first (run ./install.sh if needed).
#
# Usage: ./run_server.sh [PORT]
# Example: ./run_server.sh 8502
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default port
PORT=${1:-8501}

# Print functions
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_banner() {
    echo -e "${CYAN}"
    echo "  ____                                  _       __  __            _             "
    echo " |  _ \ _ __ ___   __ _ _ __   ___  ___(_)___  |  \/  | __ _ _ __| | _____ _ __ "
    echo " | |_) | '__/ _ \ / _\` | '_ \ / _ \/ __| / __| | |\/| |/ _\` | '__| |/ / _ \ '__|"
    echo " |  __/| | | (_) | (_| | | | | (_) \__ \ \__ \ | |  | | (_| | |  |   <  __/ |   "
    echo " |_|   |_|  \___/ \__, |_| |_|\___/|___/_|___/ |_|  |_|\__,_|_|  |_|\_\___|_|   "
    echo "                  |___/                                                          "
    echo -e "${NC}"
    echo -e "${BLUE}                  🔬 Streamlit Codebase Analyzer${NC}\n"
}

# Display banner
clear
print_banner

# ============================================================================
# Check for pixi installation
# ============================================================================
print_header "Checking requirements"

if ! command -v pixi &> /dev/null; then
    print_error "pixi is not installed or not in PATH"
    print_info ""
    print_info "Please install pixi first:"
    print_info "  curl -fsSL https://pixi.sh/install.sh | bash"
    print_info ""
    print_info "Or run the full installation script:"
    print_info "  ./install.sh"
    exit 1
fi

print_success "pixi is installed"

# ============================================================================
# Check if dependencies are installed
# ============================================================================
if [ ! -d ".pixi" ]; then
    print_error "Dependencies not installed (no .pixi directory found)"
    print_info ""
    print_info "Please install dependencies first:"
    print_info "  pixi install"
    print_info ""
    print_info "Or run the full installation script:"
    print_info "  ./install.sh"
    exit 1
fi

print_success "Dependencies are installed"

# ============================================================================
# Check if port is available
# ============================================================================
if command -v lsof &> /dev/null; then
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "Port $PORT is already in use"
        print_info ""
        print_info "Options:"
        print_info "  1. Stop the process using port $PORT"
        print_info "  2. Use a different port: ./run_server.sh 8502"
        exit 1
    fi
fi

# ============================================================================
# Launch Streamlit server
# ============================================================================
print_header "Launching Streamlit Server"

print_info "Server URL: http://localhost:$PORT"
print_info ""
print_info "The web interface will open automatically in your browser."
print_info "If it doesn't, manually navigate to: ${GREEN}http://localhost:$PORT${NC}"
print_info ""
print_info "Features:"
print_info "  📊 Dashboard - Project statistics and visualizations"
print_info "  📁 File Explorer - Browse code with syntax highlighting"
print_info "  🔍 Code Search - Full-text search with regex support"
print_info "  🔧 Analysis Tools - R file analysis and dependencies"
print_info "  📜 Git History - Commit timeline and branch info"
print_info ""
print_info "Press ${RED}Ctrl+C${NC} to stop the server."
print_info ""

# Wait a moment before launching
sleep 2

# Launch Streamlit using pixi
print_success "Starting Streamlit..."
echo ""

# Trap Ctrl+C for graceful shutdown
trap 'echo -e "\n${YELLOW}→ Shutting down Streamlit server...${NC}"; exit 0' INT

# Launch with custom port if specified
if [ "$PORT" != "8501" ]; then
    pixi run streamlit run streamlit_app.py --server.port $PORT --server.address localhost
else
    pixi run streamlit
fi

# This line only executes after Ctrl+C
echo ""
print_info "Streamlit server stopped."
