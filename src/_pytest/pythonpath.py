import sys
from typing import List

import pytest
from pytest import Config
from pytest import Parser


def pytest_addoption(parser: Parser) -> None:
    parser.addini("pythonpath", type="paths", help="Add paths to sys.path", default=[])


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(
    early_config: Config, parser: Parser, args: List[str]
) -> None:
    """`pythonpath = a b` will set `sys.path` to `[a, b, x, y, z, ...]`"""
    for path in reversed(early_config.getini("pythonpath")):
        sys.path.insert(0, str(path))
