from __future__ import annotations

import collections
import functools
import gc
import sys
import traceback
from typing import Callable
from typing import Generator
from typing import TYPE_CHECKING
import warnings

from _pytest.config import Config
import pytest


if TYPE_CHECKING:
    pass

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup


def unraisable_exception_runtest_hook() -> Generator[None]:
    try:
        yield
    finally:
        collect_unraisable()


_unraisable_exceptions: collections.deque[tuple[str, sys.UnraisableHookArgs]] = (
    collections.deque()
)


def collect_unraisable() -> None:
    errors = []
    unraisable = None
    try:
        while True:
            try:
                object_repr, unraisable = _unraisable_exceptions.pop()
            except IndexError:
                break

            if unraisable.err_msg is not None:
                err_msg = unraisable.err_msg
            else:
                err_msg = "Exception ignored in"
            msg = f"{err_msg}: {object_repr}\n\n"
            msg += "".join(
                traceback.format_exception(
                    unraisable.exc_type,
                    unraisable.exc_value,
                    unraisable.exc_traceback,
                )
            )
            try:
                warnings.warn(pytest.PytestUnraisableExceptionWarning(msg))
            except pytest.PytestUnraisableExceptionWarning as e:
                e.__cause__ = unraisable.exc_value
                errors.append(e)

        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise ExceptionGroup("multiple unraisable exception warnings", errors)
    finally:
        del errors, unraisable


def _cleanup(prev_hook: Callable[[sys.UnraisableHookArgs], object]) -> None:
    try:
        for i in range(5):
            gc.collect()
        collect_unraisable()
    finally:
        sys.unraisablehook = prev_hook


def unraisable_hook(unraisable: sys.UnraisableHookArgs) -> None:
    _unraisable_exceptions.append((repr(unraisable.object), unraisable))


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
