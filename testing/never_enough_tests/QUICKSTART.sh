#!/usr/bin/env bash

##############################################################################
# Quick Start Guide for Never Enough Tests
# Run this script to get started immediately
##############################################################################

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Never Enough Tests - Quick Start Setup             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

echo "📦 Step 1: Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    echo "❌ Error: pip not found. Please install Python and pip first."
    exit 1
fi

echo "✅ Python dependencies installed"
echo ""

echo "🔨 Step 2: Building C++ components..."
if command -v g++ &> /dev/null || command -v clang++ &> /dev/null; then
    cd cpp_components
    if [ -f "Makefile" ]; then
        make all
    else
        mkdir -p build
        g++ -std=c++17 -O2 boundary_tester.cpp -o build/boundary_tester
        g++ -std=c++17 -O2 fuzzer.cpp -o build/fuzzer
    fi
    cd ..
    echo "✅ C++ components built successfully"
else
    echo "⚠️  Warning: C++ compiler not found. C++ tests will be skipped."
    echo "   Install with: sudo apt-get install build-essential (Ubuntu/Debian)"
    echo "   or: brew install gcc (macOS)"
fi
echo ""

echo "🧪 Step 3: Running quick validation..."
pytest test_never_enough.py -k "suite_integrity" -v

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! 🎉                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Try these commands:"
echo ""
echo "  Normal mode:"
echo "    pytest test_never_enough.py -v"
echo ""
echo "  Chaos mode:"
echo "    pytest test_never_enough.py --chaos-mode --chaos-seed=42 -v"
echo ""
echo "  Parallel execution:"
echo "    pytest test_never_enough.py -n auto"
echo ""
echo "  Using orchestration scripts:"
echo "    ./scripts/never_enough_tests.sh --mode normal"
echo "    ./scripts/never_enough_tests.sh --mode chaos --seed 42"
echo "    ./scripts/never_enough_tests.sh --mode extreme --workers 4"
echo ""
echo "  Performance benchmarking:"
echo "    ./scripts/benchmark_runner.sh"
echo ""
echo "  Advanced chaos testing:"
echo "    ./scripts/chaos_runner.sh"
echo ""
echo "📖 For full documentation, see README.md"
echo ""
