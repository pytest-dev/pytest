# Never Enough Tests: Extreme Pytest Stress Testing Suite

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Pytest](https://img.shields.io/badge/pytest-7.0+-green.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

**Never Enough Tests** is an extreme stress testing suite for pytest, inspired by the chaos engineering principles of DominionOS. This project pushes pytest to its limits through:

- **Extreme fixture chains**: Deep dependency graphs and diamond patterns
- **Parametrization explosions**: Thousands of generated test cases
- **Cross-language boundaries**: C++ integration for validating subprocess handling
- **Chaos mode**: Randomized execution, environment mutations, resource stress
- **Parallel execution stress**: Testing race conditions and resource contention

## Philosophy

> "Testing frameworks must be robust under extreme conditions."

Real-world CI/CD environments are chaotic: parallel workers, resource constraints, random ordering, flaky infrastructure. This suite simulates that chaos to expose bugs that only appear under stress, ensuring pytest remains resilient.

## Project Structure

```
never_enough_tests/
├── test_never_enough.py         # Main Python test module
├── cpp_components/               # C++ boundary testing components
│   ├── boundary_tester.cpp       # Integer overflow, memory, buffer tests
│   ├── fuzzer.cpp                # Input fuzzing generator
│   └── Makefile                  # Build system
├── scripts/                      # Orchestration scripts
│   ├── never_enough_tests.sh     # Main test runner
│   ├── chaos_runner.sh           # Advanced chaos orchestration
│   └── benchmark_runner.sh       # Performance benchmarking
├── README.md                     # This file
└── CONTRIBUTING.md               # Contribution guidelines
```

## Installation

### Prerequisites

```bash
# Python dependencies
pip install pytest pytest-xdist pytest-random-order

# Optional: For coverage analysis
pip install pytest-cov coverage

# C++ compiler (GCC 7+ or Clang 5+)
sudo apt-get install build-essential  # Debian/Ubuntu
# or
brew install gcc  # macOS
```

### Building C++ Components

```bash
cd cpp_components
make all
# or manually:
g++ -std=c++17 -O2 boundary_tester.cpp -o build/boundary_tester
g++ -std=c++17 -O2 fuzzer.cpp -o build/fuzzer
```

## Usage

### Quick Start

```bash
# Run basic test suite
pytest test_never_enough.py -v

# Run with chaos mode enabled
pytest test_never_enough.py --chaos-mode --chaos-seed=12345

# Parallel execution
pytest test_never_enough.py -n auto
```

### Using Orchestration Scripts

```bash
# Normal mode
./scripts/never_enough_tests.sh --mode normal

# Chaos mode with reproducible seed
./scripts/never_enough_tests.sh --mode chaos --seed 12345

# Extreme parallel stress testing
./scripts/never_enough_tests.sh --mode extreme --workers 8 --stress 5.0

# Run all modes sequentially
./scripts/never_enough_tests.sh --mode all --build-cpp

# Advanced chaos with resource limits
./scripts/chaos_runner.sh

# Performance benchmarking
./scripts/benchmark_runner.sh
```

## Test Modes

### Normal Mode
Standard execution with controlled stress factor.

```bash
./scripts/never_enough_tests.sh --mode normal
```

### Chaos Mode
Enables randomization, environment mutations, and non-deterministic behavior.

```bash
./scripts/never_enough_tests.sh --mode chaos --seed 42
```

Features:
- Random test ordering
- Environment variable mutations
- Random execution delays
- Resource stress patterns

### Parallel Mode
Tests concurrent execution with varying worker counts.

```bash
./scripts/never_enough_tests.sh --mode parallel --workers 8
```

### Extreme Mode
Maximum chaos: parallel + random order + chaos mode + high stress factor.

```bash
./scripts/never_enough_tests.sh --mode extreme --stress 10.0
```

**Warning**: Failures expected under extreme stress. This mode validates pytest's resilience.

## Command-Line Options

### pytest Options

```bash
--chaos-mode              # Enable chaos mode
--chaos-seed=N           # Reproducible random seed
--max-depth=N            # Maximum fixture recursion depth (default: 10)
--stress-factor=F        # Stress multiplier (default: 1.0, max: 10.0)
```

### Script Options

```bash
--mode <mode>            # Test mode: normal, chaos, extreme, parallel, all
--workers <n>            # Number of parallel workers (default: auto)
--seed <n>               # Random seed for reproducibility
--stress <factor>        # Stress factor multiplier
--build-cpp              # Rebuild C++ components before testing
--no-cleanup             # Don't cleanup temporary files
--verbose                # Enable verbose output
```

## Test Categories

### 1. Extreme Fixture Chains
Tests deep fixture dependencies (5+ levels) and diamond dependency patterns.

```python
def test_deep_fixture_chain(level_5_fixture):
    # Tests 5-level deep fixture dependency
    assert level_5_fixture["level"] == 5
```

### 2. Parametrization Stress
Generates thousands of test cases through parametrize combinations.

```python
@pytest.mark.parametrize("x", range(20))
@pytest.mark.parametrize("y", range(20))
def test_parametrize_cartesian_400(x, y):
    # 400 test cases from 20x20 cartesian product
    assert x * y >= 0
```

### 3. Resource Stress Testing
- **Memory stress**: Allocates large buffers (configurable via stress factor)
- **Thread stress**: Spawns multiple concurrent threads
- **File stress**: Creates hundreds of temporary files

### 4. Cross-Language Boundary Testing
Executes C++ programs via subprocess to validate:
- Integer overflow handling
- Null pointer detection
- Memory allocation limits
- Buffer boundary conditions
- Floating-point precision

```python
def test_cpp_boundary_integer_overflow(cpp_boundary_tester):
    result = subprocess.run([str(cpp_boundary_tester), "int_overflow"], ...)
    assert result.returncode == 0
```

### 5. Fixture Scope Boundaries
Tests interaction between session, module, class, and function-scoped fixtures.

### 6. Chaos Mode Tests
50 randomized test cases with:
- Random delays
- Environment mutations
- Non-deterministic operations

## C++ Components

### boundary_tester
Validates boundary conditions difficult to test in Python:

```bash
./build/boundary_tester int_overflow       # Integer overflow
./build/boundary_tester null_pointer       # Null pointer handling
./build/boundary_tester memory_stress      # Memory allocation
./build/boundary_tester buffer_test 1024   # Buffer boundaries
./build/boundary_tester float_precision    # Float precision
./build/boundary_tester recursion_depth    # Stack overflow
./build/boundary_tester exception_handling # C++ exceptions
```

### fuzzer
Generates malformed inputs for fuzzing:

```bash
./build/fuzzer random_bytes 1000        # Random byte sequences
./build/fuzzer malformed_utf8 500       # Malformed UTF-8
./build/fuzzer extreme_numbers 10       # Extreme numeric values
./build/fuzzer json_fuzzing 20          # Malformed JSON
```

## Performance Benchmarking

```bash
./scripts/benchmark_runner.sh
```

Measures:
- Test collection time
- Execution time per test
- Memory usage patterns
- Parallel scaling efficiency (1, 2, 4, 8 workers)

Results saved in `scripts/benchmark_results/`.

## Contributing to pytest-dev/pytest

This suite is designed for contribution to the pytest repository. Follow these guidelines:

### 1. Code Quality
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include type hints where appropriate

### 2. Test Design
- Tests must be reproducible (use `--chaos-seed` for randomized tests)
- Document expected behavior under stress
- Handle failures gracefully in extreme modes

### 3. Documentation
- Explain the chaos-testing philosophy in comments
- Provide usage examples
- Document expected failure modes

### 4. Integration
- Ensure compatibility with pytest 7.0+
- Test with Python 3.8+
- Verify parallel execution with pytest-xdist

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Never Enough Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
        mode: [normal, chaos, parallel]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-xdist pytest-random-order
    
    - name: Build C++ components
      run: |
        cd cpp_components
        make all
    
    - name: Run tests
      run: |
        ./scripts/never_enough_tests.sh --mode ${{ matrix.mode }} --seed 42
```

## Known Limitations

1. **C++ compilation required**: Some tests skip if C++ compiler unavailable
2. **Resource limits**: Extreme mode may fail on resource-constrained systems
3. **Parallel execution**: Requires pytest-xdist plugin
4. **Random ordering**: Requires pytest-random-order plugin

## Troubleshooting

### Tests timeout in extreme mode
Reduce stress factor: `--stress-factor=0.5`

### Out of memory errors
Lower worker count or stress factor: `--workers 2 --stress 1.0`

### C++ compilation fails
Ensure GCC 7+ or Clang 5+ installed with C++17 support

### Random order not working
Install plugin: `pip install pytest-random-order`

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- Inspired by DominionOS chaos engineering principles
- Built for the pytest-dev/pytest community
- Designed to push testing frameworks beyond normal limits

## Contact

For questions or contributions, open an issue on the pytest-dev/pytest repository.

---

**Remember**: "Never Enough Tests" - Because robust software requires extreme validation! 🚀
