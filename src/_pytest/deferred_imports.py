"""Opt-in dependency gates recorded while importing test modules or conftests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import TYPE_CHECKING

from _pytest.outcomes import Skipped
from _pytest.stash import StashKey


if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.nodes import Item


@dataclass
class DeferredGate:
    skipped: Skipped
    filename: str
    lineno: int


@dataclass
class ImportContext:
    gates: list[DeferredGate]


_context: ContextVar[ImportContext | None] = ContextVar(
    "pytest_deferred_import", default=None
)
_gates_key = StashKey[dict[Path, list[DeferredGate]]]()
active_gate_key = StashKey[DeferredGate]()


class UnavailableModule:
    def __init__(self, skipped: Skipped) -> None:
        self._skipped = skipped

    def __getattr__(self, name: str) -> object:
        # Collection introspects objects for fixtures, marks, and test classes.
        if name.startswith("_"):
            raise AttributeError(name)
        raise self._skipped


def defer_skip(skipped: Skipped) -> UnavailableModule:
    __tracebackhide__ = True
    context = _context.get()
    if context is None:
        raise skipped
    caller = sys._getframe(2)
    context.gates.append(
        DeferredGate(skipped, caller.f_code.co_filename, caller.f_lineno)
    )
    return UnavailableModule(skipped)


@contextmanager
def collect_deferred_imports(config: Config, path: Path) -> Iterator[None]:
    context = ImportContext([])
    token = _context.set(context)
    try:
        try:
            yield
        except (Exception, Skipped):
            # If eager use or a transitive import prevents collection, retain
            # the original module-level skip rather than report a new error.
            if context.gates:
                raise context.gates[0].skipped from None
            raise
        else:
            if context.gates:
                config.stash.setdefault(_gates_key, {})[path] = context.gates
    finally:
        _context.reset(token)


def skip_if_gated(item: Item) -> None:
    for path, gates in item.config.stash.get(_gates_key, {}).items():
        if path == item.path or (
            path.name == "conftest.py" and item.path.is_relative_to(path.parent)
        ):
            gate = gates[0]
            item.stash[active_gate_key] = gate
            raise Skipped(gate.skipped.msg)
