"""Indirection for time functions.

We intentionally grab some "time" functions internally to avoid tests mocking "time" to affect
pytest runtime information (issue #185).

Fixture "mock_timing" also interacts with this module for pytest's own tests.
"""
from time import perf_counter
from time import sleep
from time import time as Time


_paused_for = 0.0
_pause_start = 0.0


def StopTimer() -> None:
    """Pause the timing.

    Pracrically, we start a measurement when the pause started
    so we can substract the diff from the final time.

    NOTE: Please don't use this with paralellized tests!
    """
    global _pause_start

    if _pause_start:
        raise Exception("Maybe you meant to call pytest.timing.StartTimer() ?")

    _pause_start = Time()


def StartTimer() -> None:
    """Continue the original timing.

    Here, we count how long did we pause for and reset the pasue start.

    NOTE: Please don't use this with paralellized tests!
    """
    global _paused_for, _pause_start

    if not _pause_start:
        raise Exception("Maybe you meant to call pytest.timing.StopTimer() ?")

    _paused_for += Time() - _pause_start
    _pause_start = 0


def time() -> float:
    return Time() - _paused_for


__all__ = ["perf_counter", "sleep", "time", "StartTimer", "StopTimer"]
