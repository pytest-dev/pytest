"""File for checking typing issues.

This file is not executed, it is only checked by mypy to ensure that
none of the code triggers any mypy errors.
"""
import pytest


# Issue #7488.
@pytest.mark.xfail(raises=RuntimeError)
def check_mark_xfail_raises() -> None:
    pass
