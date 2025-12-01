# Contributing to Never Enough Tests

Thank you for your interest in contributing to the Never Enough Tests suite for pytest! This document provides guidelines for contributing high-quality stress tests.

## Philosophy

The Never Enough Tests suite follows chaos engineering principles:

1. **Expose weaknesses through controlled experiments**
2. **Build confidence in system resilience**
3. **Learn from failures under stress**
4. **Automate chaos to run continuously**

## What Makes a Good Stress Test?

### 1. Reproducibility
All tests must be reproducible, even when using randomization:

```python
# GOOD: Uses configurable seed
@pytest.mark.parametrize("iteration", range(50))
def test_chaos_execution(iteration, chaos_config):
    random.seed(chaos_config["seed"] + iteration)
    # ... test logic

# BAD: Non-reproducible randomness
def test_chaos_bad():
    random.seed()  # No way to reproduce
```

### 2. Clear Purpose
Document WHY the test exists and WHAT boundary it explores:

```python
def test_extreme_parametrization():
    """
    Tests pytest's ability to handle 1000+ parametrized test cases.
    
    Boundary: Validates test collection and memory management with
    extreme parametrization, exposing potential O(n²) algorithms.
    
    Expected: Should complete in <30s on modern hardware.
    """
```

### 3. Graceful Degradation
Tests should handle resource constraints gracefully:

```python
def test_memory_stress(chaos_config):
    """Test memory allocation patterns."""
    stress_factor = chaos_config["stress_factor"]
    
    # Cap at reasonable maximum
    size = min(int(1000000 * stress_factor), 100000000)
    
    try:
        data = bytearray(size)
        # ... test logic
    except MemoryError:
        pytest.skip("Insufficient memory for stress test")
```

### 4. Isolation
Tests must not interfere with each other:

```python
# GOOD: Cleanup in fixture teardown
@pytest.fixture
def temp_resources(tmp_path):
    resources = create_resources(tmp_path)
    yield resources
    cleanup(resources)  # Guaranteed cleanup

# BAD: Pollutes global state
def test_bad():
    global_state["key"] = "value"  # No cleanup
```

## Contribution Categories

### 1. New Test Patterns

Add tests that explore new pytest boundaries:

- **Fixture patterns**: Circular dependencies, dynamic generation, scope mixing
- **Parametrization**: New combinations, extreme scales, complex types
- **Markers**: Custom markers, marker inheritance, filtering edge cases
- **Plugins**: Plugin interaction, hook execution order, plugin conflicts

### 2. Cross-Language Integration

Expand C++ boundary testing or add new languages:

- **Rust**: Memory safety, ownership boundaries
- **Go**: Goroutine interactions, channel chaos
- **JavaScript**: V8 integration, async boundary testing

### 3. Chaos Scenarios

New chaos modes or orchestration patterns:

- **Network chaos**: Simulated failures, latency injection
- **Filesystem chaos**: Full disk, permission errors, corruption
- **Time chaos**: Clock skew, timezone mutations
- **Signal chaos**: Random SIGSTOP/SIGCONT patterns

### 4. Performance Optimizations

Improve execution speed without losing stress coverage:

- Profiling insights
- Parallel execution improvements
- Smarter test generation

## Code Standards

### Python

Follow pytest-dev standards:

```python
# Type hints
def create_fixture(name: str, scope: str = "function") -> pytest.fixture:
    """Create a dynamic fixture."""
    pass

# Docstrings (Google style)
def complex_function(param1: int, param2: str) -> dict:
    """
    Short description.
    
    Longer explanation of what this function does and why it exists.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Dictionary containing results
    
    Raises:
        ValueError: When param1 is negative
    """
    pass

# Clear variable names
def test_fixture_scope_interaction():
    # GOOD
    session_scoped_counter = 0
    
    # BAD
    x = 0
```

### C++

Follow modern C++ practices:

```cpp
// Use smart pointers
auto buffer = std::make_unique<char[]>(size);

// RAII for resource management
class ResourceManager {
public:
    ResourceManager(size_t size) : data_(new char[size]) {}
    ~ResourceManager() { delete[] data_; }
    
private:
    char* data_;
};

// Const correctness
const std::string& get_value() const { return value_; }

// Type safety
enum class TestMode { Normal, Chaos, Extreme };
```

### Shell

Defensive bash scripting:

```bash
#!/usr/bin/env bash

# Fail fast
set -euo pipefail

# Quote variables
echo "Value: ${var}"

# Check command existence
if ! command -v pytest &> /dev/null; then
    echo "pytest not found"
    exit 1
fi

# Cleanup on exit
cleanup() {
    rm -rf "${temp_dir}"
}
trap cleanup EXIT
```

## Testing Your Contribution

Before submitting:

### 1. Run Full Test Suite

```bash
# Normal mode
./scripts/never_enough_tests.sh --mode normal

# Chaos mode with multiple seeds
for seed in 1 42 12345; do
    ./scripts/never_enough_tests.sh --mode chaos --seed $seed
done

# Parallel mode
./scripts/never_enough_tests.sh --mode parallel --workers 4
```

### 2. Verify Reproducibility

```bash
# Run twice with same seed - should produce identical results
./scripts/never_enough_tests.sh --mode chaos --seed 42 > run1.log
./scripts/never_enough_tests.sh --mode chaos --seed 42 > run2.log
diff run1.log run2.log  # Should be identical
```

### 3. Check Resource Usage

```bash
# Monitor memory usage
/usr/bin/time -v pytest test_never_enough.py

# Profile execution
python -m cProfile -o profile.stats -m pytest test_never_enough.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

### 4. Verify C++ Components

```bash
cd cpp_components
make clean
make all
make test
```

### 5. Lint and Format

```bash
# Python
black test_never_enough.py
flake8 test_never_enough.py
mypy test_never_enough.py

# C++
clang-format -i *.cpp

# Shell
shellcheck scripts/*.sh
```

## Pull Request Process

### 1. Branch Naming

- `feature/new-fixture-pattern` - New test patterns
- `chaos/network-injection` - New chaos scenarios
- `cpp/rust-integration` - Cross-language additions
- `perf/parallel-optimization` - Performance improvements
- `docs/contribution-guide` - Documentation updates

### 2. Commit Messages

Follow conventional commits:

```
feat: Add circular fixture dependency tests

Tests pytest's ability to detect and handle circular fixture
dependencies across module boundaries.

Boundary: Fixture dependency resolution
Expected: Should raise FixtureLookupError
```

### 3. PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed? What boundary does it explore?

## Testing
How was this tested? Include reproduction steps.

## Checklist
- [ ] Tests pass in normal mode
- [ ] Tests pass in chaos mode (multiple seeds)
- [ ] C++ components compile (if applicable)
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] Reproducible with `--chaos-seed`
```

### 4. Review Process

All contributions will be reviewed for:

1. **Correctness**: Tests must execute without errors in normal mode
2. **Chaos resilience**: Tests must be reproducible in chaos mode
3. **Documentation**: Clear explanations of boundaries tested
4. **Code quality**: Follows style guidelines
5. **Performance**: No unnecessary overhead in critical paths

## Advanced Topics

### Creating Dynamic Fixtures

```python
def create_fixture_factory(depth: int):
    """Factory for creating nested fixtures programmatically."""
    
    def fixture_func(*args):
        return {"depth": depth, "dependencies": len(args)}
    
    fixture_func.__name__ = f"dynamic_fixture_depth_{depth}"
    return pytest.fixture(scope="function")(fixture_func)

# Generate fixtures dynamically
for i in range(10):
    globals()[f"fixture_{i}"] = create_fixture_factory(i)
```

### Custom Markers

```python
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "boundary: Tests boundary conditions"
    )
    config.addinivalue_line(
        "markers", "chaos: Tests requiring chaos mode"
    )
```

### Hooks for Chaos Injection

```python
def pytest_runtest_setup(item):
    """Inject chaos before each test."""
    if item.config.getoption("--chaos-mode"):
        # Inject random delays, environment mutations, etc.
        inject_chaos()
```

## Questions?

- Open an issue with the `question` label
- Tag with `stress-testing` or `chaos-engineering`
- Reference specific test cases or patterns

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make pytest more resilient!** 🚀
