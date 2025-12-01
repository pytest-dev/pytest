#!/usr/bin/env bash

##############################################################################
# chaos_runner.sh
# Advanced chaos orchestration with resource limits and environment fuzzing
#
# Purpose:
# Push pytest beyond normal limits by:
# - Manipulating resource limits (ulimit)
# - Injecting random delays and failures
# - Mutating environment variables mid-execution
# - Running with different Python interpreters
# - Simulating disk/network failures
#
# This script is for EXTREME stress testing only.
##############################################################################

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_chaos() {
    echo -e "${YELLOW}[CHAOS]${NC} $*"
}

##############################################################################
# Resource Limit Chaos
##############################################################################

run_with_limited_memory() {
    log_chaos "Running with limited memory (512MB)..."
    
    # Limit virtual memory to 512MB
    ulimit -v 524288 2>/dev/null || log_chaos "Could not set memory limit (requires permissions)"
    
    pytest "$TEST_DIR/test_never_enough.py" \
        --chaos-mode \
        --stress-factor=0.5 \
        -k "memory" \
        || log_chaos "Memory-limited tests completed (failures expected)"
}

run_with_limited_files() {
    log_chaos "Running with limited file descriptors (256)..."
    
    # Limit open files
    ulimit -n 256 2>/dev/null || log_chaos "Could not set file limit"
    
    pytest "$TEST_DIR/test_never_enough.py" \
        --chaos-mode \
        -k "file" \
        || log_chaos "File-limited tests completed"
}

run_with_limited_processes() {
    log_chaos "Running with limited processes (50)..."
    
    # Limit number of processes
    ulimit -u 50 2>/dev/null || log_chaos "Could not set process limit"
    
    pytest "$TEST_DIR/test_never_enough.py" \
        --chaos-mode \
        -k "thread" \
        || log_chaos "Process-limited tests completed"
}

##############################################################################
# Environment Mutation Chaos
##############################################################################

run_with_random_environment() {
    log_chaos "Running with randomized environment variables..."
    
    # Save original environment
    local original_env=$(env)
    
    # Inject random variables
    for i in {1..50}; do
        export "RANDOM_VAR_$i"="$RANDOM"
    done
    
    # Mutate common variables
    export PYTHONHASHSEED=$RANDOM
    export LANG="C"
    export LC_ALL="C"
    
    pytest "$TEST_DIR/test_never_enough.py" \
        --chaos-mode \
        --verbose \
        || true
    
    log_chaos "Environment mutation test completed"
}

##############################################################################
# Timing Chaos
##############################################################################

run_with_random_delays() {
    log_chaos "Running with random execution delays..."
    
    # Create wrapper script that injects delays
    cat > /tmp/chaos_pytest_wrapper.sh << 'EOF'
#!/bin/bash
sleep $(echo "scale=2; $RANDOM / 32768" | bc)
exec pytest "$@"
EOF
    
    chmod +x /tmp/chaos_pytest_wrapper.sh
    
    /tmp/chaos_pytest_wrapper.sh "$TEST_DIR/test_never_enough.py" \
        --chaos-mode \
        --maxfail=10 \
        || true
    
    rm -f /tmp/chaos_pytest_wrapper.sh
    log_chaos "Random delay test completed"
}

##############################################################################
# Parallel Execution Chaos
##############################################################################

run_with_varying_workers() {
    log_chaos "Running with varying worker counts..."
    
    for workers in 1 2 4 8; do
        log_chaos "Testing with $workers workers..."
        
        pytest "$TEST_DIR/test_never_enough.py" \
            -n "$workers" \
            --chaos-mode \
            --tb=line \
            --maxfail=5 \
            || log_chaos "Worker count $workers completed (failures expected)"
        
        sleep 1
    done
}

##############################################################################
# Recursive Test Execution
##############################################################################

run_recursive_pytest() {
    log_chaos "Running recursive pytest invocations..."
    
    # Run pytest that spawns pytest (controlled depth)
    PYTEST_DEPTH=${PYTEST_DEPTH:-0}
    
    if [ "$PYTEST_DEPTH" -lt 3 ]; then
        export PYTEST_DEPTH=$((PYTEST_DEPTH + 1))
        
        log_chaos "Pytest depth: $PYTEST_DEPTH"
        
        pytest "$TEST_DIR/test_never_enough.py" \
            -k "suite_integrity" \
            --tb=line \
            || true
    fi
}

##############################################################################
# Signal Handling Chaos
##############################################################################

run_with_signal_injection() {
    log_chaos "Running with signal injection..."
    
    # Start pytest in background
    pytest "$TEST_DIR/test_never_enough.py" \
        --chaos-mode \
        --verbose &
    
    local pytest_pid=$!
    
    # Randomly send signals (non-fatal)
    sleep 2
    
    if kill -0 "$pytest_pid" 2>/dev/null; then
        log_chaos "Sending SIGUSR1..."
        kill -USR1 "$pytest_pid" 2>/dev/null || true
    fi
    
    sleep 2
    
    if kill -0 "$pytest_pid" 2>/dev/null; then
        log_chaos "Sending SIGUSR2..."
        kill -USR2 "$pytest_pid" 2>/dev/null || true
    fi
    
    # Wait for completion
    wait "$pytest_pid" || log_chaos "Pytest terminated with signals"
}

##############################################################################
# Main Chaos Loop
##############################################################################

main() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                 CHAOS RUNNER - EXTREME MODE                ║${NC}"
    echo -e "${CYAN}║                  May the odds be ever...                   ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    log_chaos "Starting chaos testing sequence..."
    log_chaos "Timestamp: $(date)"
    log_chaos "Hostname: $(hostname)"
    log_chaos "Python: $(python3 --version 2>&1)"
    
    # Run all chaos modes
    run_with_limited_memory || true
    run_with_limited_files || true
    run_with_random_environment || true
    run_with_varying_workers || true
    run_with_random_delays || true
    
    # Advanced chaos (may require permissions)
    # run_with_limited_processes || true
    # run_recursive_pytest || true
    # run_with_signal_injection || true
    
    echo ""
    log_chaos "Chaos testing sequence completed!"
    log_chaos "System survived. Pytest is resilient! 🎉"
    echo ""
}

# Execute
main "$@"
