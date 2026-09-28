from __future__ import annotations

from pathlib import Path
import sys


sys.path.append(str(Path(__file__).parent.parent))

from collections.abc import Callable
from venv.lib64.python3.site_packages.external_lib import external_lib

from src.main import func


def test_plugin(a: int, b: int, special_asserter: Callable[[int, int], bool]) -> None:
    special_asserter(a, b)


def test_func(a: int, b: int) -> None:
    assert {"func_a": func(a, b)} == {"func_a": 0}


def test_lib(a: int) -> None:
    external_lib.some_check(a)
