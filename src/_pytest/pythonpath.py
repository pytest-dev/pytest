import sys
from typing import List

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser):
    parser.addini("pythonpath", type="pathlist", help="Add paths to sys.path")


@pytest.mark.tryfirst
def pytest_load_initial_conftests(
    early_config: Config, parser: Parser, args: List[str]
):
    # `pythonpath = a b` will set `sys.path` to `[a, b, ...]`
    paths = early_config.getini("pythonpath")
    if paths:
        for path in reversed(paths):
            sys.path.insert(0, str(path))
