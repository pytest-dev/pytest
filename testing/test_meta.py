"""Test importing of all internal packages and modules.

This ensures all internal packages can be imported without needing the pytest
namespace being set, which is critical for the initialization of xdist.
"""

from __future__ import annotations

import importlib
import pkgutil
import subprocess
import sys
import types

import _pytest
from _pytest.compat import safe_getattr
from _pytest.compat import safe_isclass
from _pytest.config import Config
from _pytest.config import PytestPluginManager
from _pytest.fixtures import FixtureFunctionDefinition
from _pytest.terminal import TerminalReporter
import pytest


def _modules() -> list[str]:
    pytest_pkg: str = _pytest.__path__  # type: ignore
    return sorted(
        n
        for _, n, _ in pkgutil.walk_packages(pytest_pkg, prefix=_pytest.__name__ + ".")
    )


@pytest.mark.slow
@pytest.mark.parametrize("module", _modules())
def test_no_warnings(module: str) -> None:
    # fmt: off
    subprocess.check_call((
        sys.executable,
        "-W", "error",
        "-c", f"__import__({module!r})",
    ))
    # fmt: on


def _opted_out_holders() -> list[object]:
    """All holders carrying the ``__pytest_no_fixtures__`` opt-out marker."""
    holders: list[object] = [Config, PytestPluginManager, TerminalReporter]
    for _, name, _ in pkgutil.walk_packages(
        _pytest.__path__, prefix=_pytest.__name__ + "."
    ):
        module = importlib.import_module(name)
        if safe_getattr(module, "__pytest_no_fixtures__", False):
            holders.append(module)
    return holders


def _discoverable_fixture_names(holder: object) -> list[str]:
    """Names which ``FixtureManager.parsefactories`` would register as
    fixtures on ``holder``.

    Mirrors the detection in ``parsefactories``: fixtures are looked up on the
    module itself, or on the class for instance holders.
    """
    if not safe_isclass(holder) and not isinstance(holder, types.ModuleType):
        holder = type(holder)
    return [
        name
        for name in dir(holder)
        if type(safe_getattr(holder, name, None)) is FixtureFunctionDefinition
    ]


def test_no_fixtures_opt_out_holders_define_no_fixtures() -> None:
    """Guard for the ``__pytest_no_fixtures__`` opt-out (see #14877).

    ``FixtureManager.parsefactories`` skips fixture discovery entirely for
    holders carrying the marker, so any fixture defined on such a holder
    would silently never be collected. Fail here if that ever happens.
    """
    holders = _opted_out_holders()
    assert holders, "expected some holders to carry __pytest_no_fixtures__"
    offenders = {
        getattr(holder, "__name__", repr(holder)): _discoverable_fixture_names(holder)
        for holder in holders
    }
    offenders = {name: found for name, found in offenders.items() if found}
    assert not offenders, (
        "holders marked __pytest_no_fixtures__ define fixtures which "
        f"parsefactories would silently skip: {offenders}"
    )


def test_discoverable_fixture_names_supports_instance_holders() -> None:
    """Instance holders resolve to their class, mirroring parsefactories."""
    holder_cls = type("Plugin", (), {"my_fixture": pytest.fixture(lambda: 1)})

    assert _discoverable_fixture_names(holder_cls()) == ["my_fixture"]
    assert _discoverable_fixture_names(holder_cls) == ["my_fixture"]
