# mypy: allow-untyped-defs
from __future__ import annotations


def pytest_ignore_collect(collection_path):
    return False
