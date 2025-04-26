"""Indirection for time functions.

We intentionally grab some "time" functions internally to avoid tests mocking "time" to affect
pytest runtime information (issue #185).

Fixture "mock_timing" also interacts with this module for pytest's own tests.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from time import perf_counter
from time import sleep
from time import time
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pytest import MonkeyPatch


class Instant:
    """
    Provides a measurement of timing between different points in the code.

    Useful to compute the elapsed time between two points in time,
    using a performance counter, and the beginning/end in actual times (as seconds since epoch).

    Inspired by Rust's `std::time::Instant`.
    """

    def __init__(self) -> None:
        import _pytest.timing  # noqa: PLW0406

        self._start_perf = _pytest.timing.perf_counter()
        self._start_time = _pytest.timing.time()

    def elapsed_s(self) -> float:
        """Return the elapsed time (in seconds) since this Instant was created, using a precise clock."""
        import _pytest.timing  # noqa: PLW0406

        return _pytest.timing.perf_counter() - self._start_perf

    def interval(self) -> tuple[float, float]:
        """Return the beginning and end times of this instant, in seconds since epoch, as provided by time.time()."""
        import _pytest.timing  # noqa: PLW0406

        return self._start_time, _pytest.timing.time()

    def __repr__(self) -> str:  # pragma: no cover
        return f"Instant(start_time={self._start_time}, elapsed_s={self.elapsed_s()})"


@dataclasses.dataclass
class MockTiming:
    """Mocks _pytest.timing with a known object that can be used to control timing in tests
    deterministically.

    pytest itself should always use functions from `_pytest.timing` instead of `time` directly.

    This then allows us more control over time during testing, if testing code also
    uses `_pytest.timing` functions.

    Time is static, and only advances through `sleep` calls, thus tests might sleep over large
    numbers and obtain accurate time() calls at the end, making tests reliable and instant."""

    _current_time: float = datetime(2020, 5, 22, 14, 20, 50).timestamp()

    def sleep(self, seconds: float) -> None:
        self._current_time += seconds

    def time(self) -> float:
        return self._current_time

    def patch(self, monkeypatch: MonkeyPatch) -> None:
        from _pytest import timing  # noqa: PLW0406

        monkeypatch.setattr(timing, "sleep", self.sleep)
        monkeypatch.setattr(timing, "time", self.time)
        monkeypatch.setattr(timing, "perf_counter", self.time)


__all__ = ["perf_counter", "sleep", "time"]
