from __future__ import annotations

import collections
import functools
import gc
import sys
import traceback
from typing import Callable
from typing import Generator
from typing import NamedTuple
from typing import TYPE_CHECKING
import warnings

from _pytest.config import Config
from _pytest.tracemalloc import tracemalloc_message
import pytest


if TYPE_CHECKING:
    pass

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup


class UnraisableMeta(NamedTuple):
    msg: str
    cause_msg: str
    exc_value: BaseException | None


def unraisable_exception_runtest_hook() -> Generator[None]:
    try:
        yield
    finally:
        collect_unraisable()


_unraisable_exceptions: collections.deque[UnraisableMeta | BaseException] = (
    collections.deque()
)


def collect_unraisable() -> None:
    errors: list[pytest.PytestUnraisableExceptionWarning | RuntimeError] = []
    meta = None
    hook_error = None
    try:
        while True:
            try:
                meta = _unraisable_exceptions.pop()
            except IndexError:
                break

            if isinstance(meta, BaseException):
                hook_error = RuntimeError("Failed to process unraisable exception")
                hook_error.__cause__ = meta
                errors.append(hook_error)
                continue

            msg = meta.msg
            try:
                warnings.warn(pytest.PytestUnraisableExceptionWarning(msg))
            except pytest.PytestUnraisableExceptionWarning as e:
                if meta.exc_value is not None:
                    # exceptions have a better way to show the traceback, but
                    # warnings do not, so hide the traceback from the msg and
                    # set the cause so the traceback shows up in the right place
                    e.args = (meta.cause_msg,)
                    e.__cause__ = meta.exc_value
                errors.append(e)

        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise ExceptionGroup("multiple unraisable exception warnings", errors)
    finally:
        del errors, meta, hook_error


def _cleanup(prev_hook: Callable[[sys.UnraisableHookArgs], object]) -> None:
    try:
        for i in range(5):
            gc.collect()
        collect_unraisable()
    finally:
        sys.unraisablehook = prev_hook


def unraisable_hook(unraisable: sys.UnraisableHookArgs) -> None:
    try:
        err_msg = (
            "Exception ignored in" if unraisable.err_msg is None else unraisable.err_msg
        )
        summary = f"{err_msg}: {unraisable.object!r}"
        traceback_message = "\n\n" + "".join(
            traceback.format_exception(
                unraisable.exc_type,
                unraisable.exc_value,
                unraisable.exc_traceback,
            )
        )
        tracemalloc_tb = tracemalloc_message(unraisable.object)
        msg = summary + traceback_message + tracemalloc_tb
        cause_msg = summary + tracemalloc_tb

        _unraisable_exceptions.append(
            UnraisableMeta(
                # we need to compute these strings here as they might change after
                # the unraisablehook finishes and before the unraisable object is
                # collected by a hook
                msg=msg,
                cause_msg=cause_msg,
                exc_value=unraisable.exc_value,
            )
        )
    except BaseException as e:
        _unraisable_exceptions.append(e)


def pytest_configure(config: Config) -> None:
    prev_hook = sys.unraisablehook
    config.add_cleanup(functools.partial(_cleanup, prev_hook))
    sys.unraisablehook = unraisable_hook


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_setup() -> Generator[None]:
    yield from unraisable_exception_runtest_hook()


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_call() -> Generator[None]:
    yield from unraisable_exception_runtest_hook()


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_teardown() -> Generator[None]:
    yield from unraisable_exception_runtest_hook()
