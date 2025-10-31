#!/bin/bash

# ============================================================================
# Prognosis Marker - Automated Installation Script
# ============================================================================
# This script automates the installation of all dependencies and launches
# the Streamlit codebase analyzer web interface.
#
# Usage: ./install.sh
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
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

# ============================================================================
# Step 1: Check for pixi installation
# ============================================================================
print_header "Step 1: Checking for pixi installation"

if command -v pixi &> /dev/null; then
    PIXI_VERSION=$(pixi --version)
    print_success "pixi is already installed: $PIXI_VERSION"
else
    print_info "pixi is not installed. Installing pixi..."

    # Check operating system
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        # Install pixi using the official installer
        curl -fsSL https://pixi.sh/install.sh | bash

        # Add pixi to PATH for current session (works on both macOS and Linux)
        # pixi installs to ~/.pixi/bin by default
        export PATH="$HOME/.pixi/bin:$PATH"

        # Verify pixi binary exists
        if [ -f "$HOME/.pixi/bin/pixi" ]; then
            print_success "pixi installed successfully to $HOME/.pixi/bin"
        else
            print_error "pixi binary not found after installation"
            print_info "Please check pixi installation: https://pixi.sh/latest/#installation"
            exit 1
        fi
    else
        print_error "Unsupported operating system. Please install pixi manually from https://pixi.sh"
        exit 1
    fi
fi

# Verify pixi is accessible
if ! command -v pixi &> /dev/null; then
    print_error "pixi installation failed or not in PATH"
    print_info "Please install pixi manually: https://pixi.sh/latest/#installation"
    print_info "Then run this script again."
    exit 1
fi

# ============================================================================
# Step 2: Install project dependencies
# ============================================================================
print_header "Step 2: Installing project dependencies (R and Python)"

print_info "Running: pixi install"
print_info "This may take a few minutes on first run..."

if pixi install; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    print_info "Try running manually: pixi install"
    exit 1
fi

# ============================================================================
# Step 3: Install additional R packages (optional)
# ============================================================================
print_header "Step 3: Installing additional R packages from CRAN"

print_info "Running: pixi run install-r-packages"
print_info "This installs CRAN packages not available in conda-forge..."

if pixi run install-r-packages; then
    print_success "R packages installed successfully"
else
    print_error "Warning: Some R packages may have failed to install"
    print_info "This is usually okay if you only need the Streamlit analyzer"
fi

# ============================================================================
# Step 4: Launch Streamlit server
# ============================================================================
print_header "Step 4: Launching Streamlit Codebase Analyzer"

print_info "Starting Streamlit server on http://localhost:8501"
print_info ""
print_info "The web interface will open automatically in your browser."
print_info "If it doesn't open, manually navigate to: http://localhost:8501"
print_info ""
print_info "Press Ctrl+C to stop the server."
print_info ""

# Wait a moment before launching
sleep 2

# Launch Streamlit (this will block until Ctrl+C)
print_success "Launching Streamlit..."
echo ""

pixi run streamlit

# This line only executes after Ctrl+C
echo ""
print_info "Streamlit server stopped."
