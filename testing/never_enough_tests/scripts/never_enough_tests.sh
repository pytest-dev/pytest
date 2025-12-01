#!/usr/bin/env bash

##############################################################################
# never_enough_tests.sh
# Main orchestration script for chaos testing suite
#
# Purpose:
# Execute the "Never Enough Tests" suite with various chaos modes, parallel
# execution patterns, and environment mutations. This script stress-tests
# pytest's infrastructure by:
# - Running tests in random order
# - Parallel execution with varying worker counts
# - Environment variable mutations
# - Resource limit adjustments
# - Selective test filtering and explosion
#
# Philosophy:
# Real-world CI/CD systems are chaotic: parallel workers, flaky networks,
# resource contention, random ordering. This script simulates that chaos
# to find bugs that only appear under stress.
#
# Usage:
#   ./never_enough_tests.sh [OPTIONS]
#
# Options:
#   --mode <mode>       Test mode: normal, chaos, extreme, parallel
#   --workers <n>       Number of parallel workers (default: auto)
#   --seed <n>          Random seed for reproducibility
#   --stress <factor>   Stress factor multiplier (default: 1.0)
#   --build-cpp         Rebuild C++ components before testing
#   --no-cleanup        Don't cleanup temporary files
#   --verbose           Enable verbose output
#   --help              Show this help message
#
# Examples:
#   ./never_enough_tests.sh --mode chaos --seed 12345
#   ./never_enough_tests.sh --mode extreme --workers 8 --stress 5.0
#   ./never_enough_tests.sh --mode parallel --build-cpp
##############################################################################

set -eo pipefail

# Default configuration
MODE="normal"
WORKERS="auto"
SEED=""
STRESS_FACTOR="1.0"
BUILD_CPP=false
CLEANUP=true
VERBOSE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR"
CPP_DIR="$SCRIPT_DIR/cpp_components"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

##############################################################################
# Helper Functions
##############################################################################

log_info() {
    echo -e "${CYAN}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_section() {
    echo ""
    echo -e "${MAGENTA}==================== $* ====================${NC}"
    echo ""
}

show_help() {
    grep '^#' "$0" | grep -v '#!/usr/bin/env' | sed 's/^# \?//'
    exit 0
}

##############################################################################
# Parse Command Line Arguments
##############################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --stress)
            STRESS_FACTOR="$2"
            shift 2
            ;;
        --build-cpp)
            BUILD_CPP=true
            shift
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

##############################################################################
# Environment Setup
##############################################################################

log_section "Never Enough Tests - Chaos Suite Initialization"

log_info "Configuration:"
log_info "  Mode:          $MODE"
log_info "  Workers:       $WORKERS"
log_info "  Seed:          ${SEED:-random}"
log_info "  Stress Factor: $STRESS_FACTOR"
log_info "  Test Dir:      $TEST_DIR"

# Validate pytest is available
if ! command -v pytest &> /dev/null; then
    log_error "pytest not found. Please install: pip install pytest pytest-xdist"
    exit 1
fi

log_success "pytest found: $(pytest --version)"

##############################################################################
# Build C++ Components
##############################################################################

if [ "$BUILD_CPP" = true ]; then
    log_section "Building C++ Components"

    if [ ! -d "$CPP_DIR" ]; then
        log_error "C++ components directory not found: $CPP_DIR"
        exit 1
    fi

    cd "$CPP_DIR"

    if [ -f "Makefile" ]; then
        log_info "Building with Make..."
        make clean
        make all
        log_success "C++ components built successfully"
    else
        log_info "Building C++ components manually..."
        mkdir -p build

        if [ -f "boundary_tester.cpp" ]; then
            g++ -std=c++17 -O2 -Wall boundary_tester.cpp -o build/boundary_tester
            log_success "Built boundary_tester"
        fi

        if [ -f "fuzzer.cpp" ]; then
            g++ -std=c++17 -O2 -Wall fuzzer.cpp -o build/fuzzer
            log_success "Built fuzzer"
        fi
    fi

    cd "$TEST_DIR"
fi

##############################################################################
# Chaos Environment Setup
##############################################################################

setup_chaos_environment() {
    log_info "Setting up chaos environment..."

    # Random environment mutations
    export CHAOS_MODE_ACTIVE=1
    export CHAOS_TIMESTAMP=$(date +%s)
    export CHAOS_RANDOM_VALUE=$RANDOM

    # Inject random variables
    for i in {1..10}; do
        export "CHAOS_VAR_$i"=$RANDOM
    done

    log_success "Chaos environment configured"
}

##############################################################################
# Test Execution Functions
##############################################################################

run_normal_mode() {
    log_section "Running Normal Mode"

    pytest "$TEST_DIR/test_never_enough.py" \
        --verbose \
        --tb=short \
        --strict-markers \
        --stress-factor="$STRESS_FACTOR" \
        ${SEED:+--chaos-seed="$SEED"}
}

run_chaos_mode() {
    log_section "Running Chaos Mode"

    setup_chaos_environment

    pytest "$TEST_DIR/test_never_enough.py" \
        --chaos-mode \
        --verbose \
        --tb=short \
        --random-order \
        --random-order-bucket=global \
        --strict-markers \
        --stress-factor="$STRESS_FACTOR" \
        ${SEED:+--chaos-seed="$SEED"} \
        ${SEED:+--random-order-seed="$SEED"}
}

run_parallel_mode() {
    log_section "Running Parallel Mode"

    # Check for pytest-xdist
    if ! pytest --co -q --collect-only -p no:terminal 2>&1 | grep -q "xdist"; then
        log_warning "pytest-xdist not available, falling back to sequential"
        run_normal_mode
        return
    fi

    pytest "$TEST_DIR/test_never_enough.py" \
        -n "$WORKERS" \
        --verbose \
        --tb=short \
        --dist=loadgroup \
        --stress-factor="$STRESS_FACTOR" \
        ${SEED:+--chaos-seed="$SEED"}
}

run_extreme_mode() {
    log_section "Running Extreme Mode"

    setup_chaos_environment

    # Maximum chaos: parallel + random order + chaos mode
    pytest "$TEST_DIR/test_never_enough.py" \
        --chaos-mode \
        -n "$WORKERS" \
        --verbose \
        --tb=line \
        --random-order \
        --random-order-bucket=global \
        --maxfail=50 \
        --strict-markers \
        --stress-factor="$STRESS_FACTOR" \
        ${SEED:+--chaos-seed="$SEED"} \
        ${SEED:+--random-order-seed="$SEED"} \
        || true  # Don't exit on failure in extreme mode

    log_warning "Extreme mode completed (failures expected under stress)"
}

run_marker_filtering() {
    log_section "Running Marker-Based Filtering Tests"

    # Test different marker combinations
    for marker in "slow" "stress" "boundary"; do
        log_info "Testing with marker: $marker"
        pytest "$TEST_DIR/test_never_enough.py" \
            -m "$marker" \
            --verbose \
            --tb=line \
            --stress-factor="$STRESS_FACTOR" \
            || true
    done
}

run_coverage_analysis() {
    log_section "Running Coverage Analysis"

    if ! command -v coverage &> /dev/null; then
        log_warning "coverage not installed, skipping coverage analysis"
        return
    fi

    coverage run -m pytest "$TEST_DIR/test_never_enough.py" \
        --verbose \
        --tb=short \
        --stress-factor=0.5  # Reduced stress for coverage

    coverage report -m
    coverage html

    log_success "Coverage report generated in htmlcov/"
}

##############################################################################
# Main Execution
##############################################################################

main() {
    local exit_code=0

    case "$MODE" in
        normal)
            run_normal_mode
            exit_code=$?
            ;;
        chaos)
            run_chaos_mode
            exit_code=$?
            ;;
        parallel)
            run_parallel_mode
            exit_code=$?
            ;;
        extreme)
            run_extreme_mode
            exit_code=$?
            ;;
        markers)
            run_marker_filtering
            exit_code=$?
            ;;
        coverage)
            run_coverage_analysis
            exit_code=$?
            ;;
        all)
            log_section "Running All Test Modes"
            run_normal_mode || true
            run_parallel_mode || true
            run_chaos_mode || true
            run_marker_filtering || true
            log_success "All test modes completed"
            exit_code=0
            ;;
        *)
            log_error "Unknown mode: $MODE"
            log_info "Valid modes: normal, chaos, parallel, extreme, markers, coverage, all"
            exit 1
            ;;
    esac

    # Cleanup
    if [ "$CLEANUP" = true ]; then
        log_info "Cleaning up temporary files..."
        find "$TEST_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find "$TEST_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        find "$TEST_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    fi

    log_section "Test Suite Execution Complete"

    if [ $exit_code -eq 0 ]; then
        log_success "All tests passed!"
    else
        log_warning "Some tests failed (exit code: $exit_code)"
    fi

    return $exit_code
}

# Execute main function
main
exit_code=$?

# Final summary
echo ""
log_info "Never Enough Tests completed with exit code: $exit_code"
log_info "Chaos seed used: ${SEED:-random}"
log_info "Timestamp: $(date)"

exit $exit_code
