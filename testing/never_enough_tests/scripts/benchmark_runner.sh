#!/usr/bin/env bash

##############################################################################
# benchmark_runner.sh
# Performance benchmarking for pytest under stress
#
# Purpose:
# Measure pytest performance metrics under various loads:
# - Test collection time
# - Execution time per test
# - Memory usage patterns
# - Parallel scaling efficiency
# - Fixture overhead
##############################################################################

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$SCRIPT_DIR/benchmark_results"

mkdir -p "$RESULTS_DIR"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

log_bench() {
    echo -e "${CYAN}[BENCH]${NC} $*"
}

##############################################################################
# Benchmark Functions
##############################################################################

benchmark_collection_time() {
    log_bench "Benchmarking test collection time..."
    
    local output_file="$RESULTS_DIR/collection_time_$(date +%s).txt"
    
    time pytest "$TEST_DIR/test_never_enough.py" \
        --collect-only \
        --quiet \
        2>&1 | tee "$output_file"
    
    log_bench "Collection benchmark saved to $output_file"
}

benchmark_execution_time() {
    log_bench "Benchmarking execution time..."
    
    local output_file="$RESULTS_DIR/execution_time_$(date +%s).txt"
    
    pytest "$TEST_DIR/test_never_enough.py" \
        --durations=20 \
        --quiet \
        2>&1 | tee "$output_file"
    
    log_bench "Execution benchmark saved to $output_file"
}

benchmark_parallel_scaling() {
    log_bench "Benchmarking parallel scaling..."
    
    local output_file="$RESULTS_DIR/parallel_scaling_$(date +%s).txt"
    
    echo "Worker Count | Execution Time" > "$output_file"
    echo "-------------|---------------" >> "$output_file"
    
    for workers in 1 2 4 8; do
        log_bench "Testing with $workers workers..."
        
        local start_time=$(date +%s)
        
        pytest "$TEST_DIR/test_never_enough.py" \
            -n "$workers" \
            --quiet \
            || true
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo "$workers | ${duration}s" >> "$output_file"
        
        log_bench "$workers workers: ${duration}s"
    done
    
    log_bench "Parallel scaling results saved to $output_file"
    cat "$output_file"
}

benchmark_memory_usage() {
    log_bench "Benchmarking memory usage..."
    
    local output_file="$RESULTS_DIR/memory_usage_$(date +%s).txt"
    
    if command -v /usr/bin/time &> /dev/null; then
        /usr/bin/time -v pytest "$TEST_DIR/test_never_enough.py" \
            --quiet \
            2>&1 | tee "$output_file"
    else
        log_bench "GNU time not available, using basic timing"
        time pytest "$TEST_DIR/test_never_enough.py" --quiet 2>&1 | tee "$output_file"
    fi
    
    log_bench "Memory benchmark saved to $output_file"
}

##############################################################################
# Main
##############################################################################

main() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}    Pytest Performance Benchmarking     ${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    
    benchmark_collection_time
    echo ""
    
    benchmark_execution_time
    echo ""
    
    benchmark_parallel_scaling
    echo ""
    
    benchmark_memory_usage
    echo ""
    
    log_bench "All benchmarks completed!"
    log_bench "Results saved in: $RESULTS_DIR"
}

main "$@"
