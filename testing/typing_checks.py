# mypy: allow-untyped-defs
"""File for checking typing issues.

This file is not executed, it is only checked by mypy to ensure that
none of the code triggers any mypy errors.
"""

from __future__ import annotations

import contextlib
from typing import Literal
from typing import Optional

from typing_extensions import assert_type

import pytest
from pytest import MonkeyPatch
from pytest import TestReport


# Issue #7488.
@pytest.mark.xfail(raises=RuntimeError)
def check_mark_xfail_raises() -> None:
    pass


# Issue #7494.
@pytest.fixture(params=[(0, 0), (1, 1)], ids=lambda x: str(x[0]))
def check_fixture_ids_callable() -> None:
    pass


# Issue #7494.
@pytest.mark.parametrize("func", [str, int], ids=lambda x: str(x.__name__))
def check_parametrize_ids_callable(func) -> None:
    pass


# Issue #10999.
def check_monkeypatch_typeddict(monkeypatch: MonkeyPatch) -> None:
    from typing import TypedDict

    class Foo(TypedDict):
        x: int
        y: float

    a: Foo = {"x": 1, "y": 3.14}
    monkeypatch.setitem(a, "x", 2)
    monkeypatch.delitem(a, "y")


def check_raises_is_a_context_manager(val: bool) -> None:
    with pytest.raises(RuntimeError) if val else contextlib.nullcontext() as excinfo:
        pass
    assert_type(excinfo, Optional[pytest.ExceptionInfo[RuntimeError]])


# Issue #12941.
def check_testreport_attributes(report: TestReport) -> None:
    assert_type(report.when, Literal["setup", "call", "teardown"])
    assert_type(report.location, tuple[str, Optional[int], str])
