# mypy: allow-untyped-defs
from __future__ import annotations


def pytest_configure(config):
    import pytest

    raise pytest.UsageError("hello")


def pytest_unconfigure(config):
    print("pytest_unconfigure_called")
