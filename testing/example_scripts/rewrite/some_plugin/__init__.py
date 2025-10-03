from __future__ import annotations

from typing import Callable

import pytest


@pytest.fixture
def special_asserter() -> Callable[[int, int], None]:
    def special_assert(a: int, b: int) -> None:
        assert {"plugin_a": a} == {"plugin_b": b}

    return special_assert
