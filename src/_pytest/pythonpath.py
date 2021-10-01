import sys
from typing import List

import pytest
from pytest import Config
from pytest import Parser


added_paths: List[str]


def pytest_addoption(parser: Parser) -> None:
    parser.addini("pythonpath", type="paths", help="Add paths to sys.path", default=[])


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config: Config) -> None:
    global added_paths
    added_paths = [str(p) for p in early_config.getini("pythonpath")]
    # `pythonpath = a b` will set `sys.path` to `[a, b, x, y, z, ...]`
    for path in reversed(added_paths):
        sys.path.insert(0, path)


def pytest_unconfigure() -> None:
    global added_paths
    for path in added_paths:
        sys.path.remove(path)
