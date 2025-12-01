"""
Conftest: Shared fixtures and configuration for Never Enough Tests

This file provides shared fixtures, hooks, and configuration used across
all test modules in the Never Enough Tests suite.
"""

import os
import random
import sys
import time
from pathlib import Path

import pytest


# ============================================================================
# SESSION-LEVEL CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure custom markers and settings."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time (>1s)"
    )
    config.addinivalue_line(
        "markers", "stress: Resource-intensive stress tests"
    )
    config.addinivalue_line(
        "markers", "boundary: Boundary condition tests"
    )
    config.addinivalue_line(
        "markers", "chaos: Tests requiring --chaos-mode flag"
    )
    config.addinivalue_line(
        "markers", "cpp: Tests requiring C++ components"
    )
    config.addinivalue_line(
        "markers", "parametrize_heavy: Tests with 100+ parametrized cases"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on configuration."""
    chaos_mode = config.getoption("--chaos-mode", default=False)
    
    # Skip chaos tests if not in chaos mode
    if not chaos_mode:
        skip_chaos = pytest.mark.skip(reason="Requires --chaos-mode flag")
        for item in items:
            if "chaos" in item.keywords:
                item.add_marker(skip_chaos)
    
    # Check for C++ components
    cpp_dir = Path(__file__).parent / "cpp_components" / "build"
    cpp_available = (
        (cpp_dir / "boundary_tester").exists() or
        (cpp_dir / "boundary_tester.exe").exists()
    )
    
    if not cpp_available:
        skip_cpp = pytest.mark.skip(reason="C++ components not built")
        for item in items:
            if "cpp" in item.keywords:
                item.add_marker(skip_cpp)


# ============================================================================
# PYTEST HOOKS FOR CHAOS INJECTION
# ============================================================================

def pytest_runtest_setup(item):
    """Hook executed before each test."""
    if item.config.getoption("--chaos-mode", default=False):
        # Inject small random delay in chaos mode
        if random.random() < 0.1:  # 10% chance
            time.sleep(random.uniform(0, 0.05))


def pytest_runtest_teardown(item):
    """Hook executed after each test."""
    # Force garbage collection after each test to detect leaks
    import gc
    gc.collect()


# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def project_root():
    """Path to the project root directory."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def cpp_build_dir(project_root):
    """Path to C++ build directory."""
    return project_root / "cpp_components" / "build"


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Path to test data directory."""
    data_dir = project_root / "test_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def execution_timer():
    """Fixture that times test execution."""
    start = time.time()
    yield
    duration = time.time() - start
    # Could log or collect metrics here
    assert duration >= 0


@pytest.fixture(scope="function")
def isolated_environment(monkeypatch):
    """Fixture that provides isolated environment variables."""
    # Save original environment
    original_env = dict(os.environ)
    
    yield monkeypatch
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="session")
def system_info():
    """Fixture providing system information for debugging."""
    return {
        "platform": sys.platform,
        "python_version": sys.version,
        "python_implementation": sys.implementation.name,
        "cpu_count": os.cpu_count(),
    }


# ============================================================================
# REPORTING HOOKS
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to customize test result reporting.
    Useful for collecting chaos mode statistics.
    """
    outcome = yield
    report = outcome.get_result()
    
    # Add custom attributes to report
    if hasattr(item, "config"):
        report.chaos_mode = item.config.getoption("--chaos-mode", default=False)
        report.chaos_seed = item.config.getoption("--chaos-seed", default=None)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom summary section to test output."""
    if config.getoption("--chaos-mode", default=False):
        terminalreporter.section("Chaos Mode Summary")
        terminalreporter.write_line(
            f"Chaos seed: {config.getoption('--chaos-seed', default='random')}"
        )
        terminalreporter.write_line(
            f"Stress factor: {config.getoption('--stress-factor', default=1.0)}"
        )
