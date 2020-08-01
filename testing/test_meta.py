"""
Test importing of all internal packages and modules.

This ensures all internal packages can be imported without needing the pytest
namespace being set, which is critical for the initialization of xdist.
"""
import pkgutil
import subprocess
import sys
from typing import List

import _pytest
import pytest


def _modules() -> List[str]:
    pytest_pkg = _pytest.__path__  # type: str  # type: ignore
    return sorted(
        n
        for _, n, _ in pkgutil.walk_packages(pytest_pkg, prefix=_pytest.__name__ + ".")
    )


@pytest.mark.slow
@pytest.mark.parametrize("module", _modules())
def test_no_warnings(module: str) -> None:
    # fmt: off
    subprocess.check_call((
        sys.executable,
        "-W", "error",
        # https://github.com/pytest-dev/pytest/issues/5901
        "-W", "ignore:The usage of `cmp` is deprecated and will be removed on or after 2021-06-01.  Please use `eq` and `order` instead.:DeprecationWarning",  # noqa: E501
        "-c", "__import__({!r})".format(module),
    ))
    # fmt: on


def test_version_tuple():
    fields = pytest.__version__.split(".")
    assert pytest.version_tuple()[:2] == (int(fields[0]), int(fields[1]))


@pytest.mark.parametrize(
    "v, expected",
    [
        ("6.0.0", (6, 0, 0, "", "")),
        ("6.0.0rc1", (6, 0, 0, "rc1", "")),
        ("6.23.1.dev39+ga", (6, 23, 1, "", "dev39+ga")),
        ("6.23.1rc2.dev39+ga", (6, 23, 1, "rc2", "dev39+ga")),
    ],
)
def test_passe_version_tuple(v, expected):
    assert _pytest.parse_version(v) == expected
