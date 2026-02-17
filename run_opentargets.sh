#!/bin/bash
# ============================================================================
# Run binary and survival analysis for all TCGA datasets with Open Targets
# evidence-based gene filtering
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
}

# Add pixi to PATH if it exists
if [ -f "$HOME/.pixi/bin/pixi" ]; then
    export PATH="$HOME/.pixi/bin:$PATH"
fi

# Check if pixi is installed
if ! command -v pixi &> /dev/null; then
    print_error "pixi is not installed or not in PATH"
    print_info "Please run: ./install.sh"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".pixi" ]; then
    print_error "Dependencies not installed"
    print_info "Please run: pixi install && pixi run install-r-packages"
    exit 1
fi

# Get all Open Targets config files
CONFIG_FILES=(config/TCGA_*_opentargets_analysis.yaml)

# Check if config files exist
if [ ! -f "${CONFIG_FILES[0]}" ]; then
    print_error "No Open Targets config files found in ./config/"
    print_info "Please run:"
    print_info "  python3 fetch_opentargets_genes.py"
    print_info "  python3 generate_opentargets_configs.py"
    exit 1
fi

# Count total datasets
TOTAL=${#CONFIG_FILES[@]}
print_header "Running Open Targets Evidence-Filtered Analysis for $TOTAL TCGA Datasets"

# Initialize counters
BINARY_SUCCESS_COUNT=0
BINARY_FAIL_COUNT=0
SURVIVAL_SUCCESS_COUNT=0
SURVIVAL_FAIL_COUNT=0
BINARY_FAILED_DATASETS=()
SURVIVAL_FAILED_DATASETS=()

# Create results directory
mkdir -p results

# Process each dataset
for i in "${!CONFIG_FILES[@]}"; do
    CONFIG="${CONFIG_FILES[$i]}"
    DATASET=$(basename "$CONFIG" _opentargets_analysis.yaml)
    CURRENT=$((i + 1))

    print_header "[$CURRENT/$TOTAL] Processing: $DATASET (Open Targets filtered)"
    print_info "Config: $CONFIG"

    # Run binary analysis
    print_info "Running binary analysis: pixi run binary -- --config $CONFIG"
    print_info "Output: results/${DATASET}_opentargets/binary"
    if pixi run binary -- --config "$CONFIG" 2>&1; then
        print_success "$DATASET binary analysis completed"
        BINARY_SUCCESS_COUNT=$((BINARY_SUCCESS_COUNT + 1))
    else
        EXIT_CODE=$?
        print_error "$DATASET binary analysis failed (exit code: $EXIT_CODE)"
        BINARY_FAIL_COUNT=$((BINARY_FAIL_COUNT + 1))
        BINARY_FAILED_DATASETS+=("$DATASET")
    fi

    echo ""

    # Run survival analysis
    print_info "Running survival analysis: pixi run survival -- --config $CONFIG"
    print_info "Output: results/${DATASET}_opentargets/survival"
    if pixi run survival -- --config "$CONFIG" 2>&1; then
        print_success "$DATASET survival analysis completed"
        SURVIVAL_SUCCESS_COUNT=$((SURVIVAL_SUCCESS_COUNT + 1))
    else
        EXIT_CODE=$?
        print_error "$DATASET survival analysis failed (exit code: $EXIT_CODE)"
        SURVIVAL_FAIL_COUNT=$((SURVIVAL_FAIL_COUNT + 1))
        SURVIVAL_FAILED_DATASETS+=("$DATASET")
    fi

    echo ""
done

# Print summary
print_header "Open Targets Analysis Summary"
echo -e "${BLUE}Binary Analysis:${NC}"
echo -e "  ${GREEN}✓ Successful: $BINARY_SUCCESS_COUNT${NC}"
echo -e "  ${RED}✗ Failed: $BINARY_FAIL_COUNT${NC}"
echo ""
echo -e "${BLUE}Survival Analysis:${NC}"
echo -e "  ${GREEN}✓ Successful: $SURVIVAL_SUCCESS_COUNT${NC}"
echo -e "  ${RED}✗ Failed: $SURVIVAL_FAIL_COUNT${NC}"
echo ""

EXIT_CODE=0
if [ $BINARY_FAIL_COUNT -gt 0 ]; then
    print_error "Failed binary analyses:"
    for dataset in "${BINARY_FAILED_DATASETS[@]}"; do
        echo "  - $dataset"
    done
    EXIT_CODE=1
fi

if [ $SURVIVAL_FAIL_COUNT -gt 0 ]; then
    print_error "Failed survival analyses:"
    for dataset in "${SURVIVAL_FAILED_DATASETS[@]}"; do
        echo "  - $dataset"
    done
    EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
    print_success "All Open Targets analyses completed successfully!"
fi

exit $EXIT_CODE
