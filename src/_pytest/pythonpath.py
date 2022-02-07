import sys

import pytest
from _pytest.deprecated import PYTHON_PATHS_INI
from _pytest.deprecated import SITE_DIRS_INI
from pytest import Config
from pytest import Parser


def pytest_addoption(parser: Parser) -> None:
    parser.addini("pythonpath", type="paths", help="Add paths to sys.path", default=[])
    parser.addini(
        "python_paths", type="paths", help="Deprecated alias for pythonpath", default=[]
    )
    parser.addini(
        "site_dirs",
        type="paths",
        help="Deprecated: directory paths to add to via site.addsitedir(path)",
        default=[],
    )


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config: Config) -> None:
    pythonpath = early_config.getini("pythonpath")
    python_paths = early_config.getini("python_paths")
    if python_paths:
        early_config.issue_config_time_warning(PYTHON_PATHS_INI, 2)
        if not pythonpath:
            pythonpath = python_paths
    # `pythonpath = a b` will set `sys.path` to `[a, b, x, y, z, ...]`
    for path in reversed(pythonpath):
        sys.path.insert(0, str(path))

    site_dirs = early_config.getini("site_dirs")
    if site_dirs:
        early_config.issue_config_time_warning(SITE_DIRS_INI, 2)

        import site

        for path in site_dirs:
            site.addsitedir(str(path))


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config: Config) -> None:
    pythonpath = config.getini("pythonpath")
    python_paths = config.getini("python_paths")
    if python_paths and not pythonpath:
        pythonpath = python_paths
    for path in pythonpath:
        path_str = str(path)
        if path_str in sys.path:
            sys.path.remove(path_str)
