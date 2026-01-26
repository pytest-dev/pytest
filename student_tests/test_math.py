from __future__ import annotations

from student_src.math_utils import add
from student_src.math_utils import divide

import pytest


def test_add():
    assert add(2, 3) == 5


def test_divide():
    assert divide(10, 2) == 5


def test_divide_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
