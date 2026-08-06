"""Nested configs and in-memory collection for pytest-under-pytest testing.

EXPERIMENTAL: internal API, no backwards-compatibility guarantees.

This package lets a test build a hermetic nested pytest configuration from
declarative data (:class:`ConfigSpec`), collect test items from in-memory
python objects instead of files on disk, run them through the standard
runtest protocol, and assert on typed report objects (:class:`RunRecord`)
instead of glob-matching rendered terminal output.

Known limitations (by design, for now):

* Scenario configs never load conftest files; pass plugin objects via
  ``ConfigSpec.extra_plugins`` instead.
* The ``capture`` and ``terminal`` plugins are not loaded by default:
  ``capsys``/``capfd`` are unavailable inside scenario tests and no
  terminal output exists. Capture nesting is a planned follow-up.
* Assertion rewriting is not applied to scenario sources; sources defined
  in the host test suite's own files are already rewritten by the host.
* Sources without real code objects (``exec``'d, lambdas) degrade
  ``reportinfo``/traceback quality.
* Process-global warning filters active around the scenario (e.g. the
  host suite's ``filterwarnings = error``) are inherited; a scenario's
  own ``inicfg={"filterwarnings": [...]}`` takes precedence over them.
"""

from __future__ import annotations

from collections.abc import Iterator
import contextlib
import pathlib

from _pytest.config import Config
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.scenario.collection import collect_objects
from _pytest.scenario.collection import fake_module
from _pytest.scenario.collection import running_session
from _pytest.scenario.collection import ScenarioModule
from _pytest.scenario.collection import Source
from _pytest.scenario.config import ConfigSpec
from _pytest.scenario.config import configured
from _pytest.scenario.config import DEFAULT_SCENARIO_PLUGINS
from _pytest.scenario.results import ItemRunRecord
from _pytest.scenario.results import run_items
from _pytest.scenario.results import RunRecord


__all__ = [
    "DEFAULT_SCENARIO_PLUGINS",
    "ConfigSpec",
    "ItemRunRecord",
    "RunRecord",
    "Scenario",
    "ScenarioModule",
    "Source",
    "collect_objects",
    "collect_tests",
    "configured",
    "fake_module",
    "run_items",
    "run_tests",
    "running_session",
    "scenario",
]


def _resolve_spec(spec: ConfigSpec | None, rootpath: pathlib.Path | None) -> ConfigSpec:
    if spec is None:
        spec = ConfigSpec(rootpath=rootpath)
    elif rootpath is not None and spec.rootpath is None:
        spec = spec.replace(rootpath=rootpath)
    return spec


def run_tests(
    *sources: Source,
    rootpath: pathlib.Path | None = None,
    spec: ConfigSpec | None = None,
    name: str = "scenario_module",
) -> RunRecord:
    """Collect and run the given in-memory sources in a nested config;
    return the structured results."""
    with scenario(*sources, rootpath=rootpath, spec=spec, name=name) as s:
        s.collect()
        return s.run()


def collect_tests(
    *sources: Source,
    rootpath: pathlib.Path | None = None,
    spec: ConfigSpec | None = None,
    name: str = "scenario_module",
) -> list[Item]:
    """Collect (only) the given in-memory sources; return the items.

    The nested config and session are torn down before returning; the
    items remain usable for structural assertions (names, nodeids, marks).
    """
    with scenario(*sources, rootpath=rootpath, spec=spec, name=name) as s:
        return s.collect()


class Scenario:
    """An entered scenario: a configured nested config plus a running
    session, over which sources can be collected and run stepwise."""

    def __init__(
        self, config: Config, session: Session, sources: tuple[Source, ...], name: str
    ) -> None:
        self.config = config
        self.session = session
        self._sources = sources
        self._name = name
        self._collected = False

    def collect(self, *sources: Source) -> list[Item]:
        """Collect the scenario's sources (plus any given extra ones)."""
        self._collected = True
        return collect_objects(self.session, *self._sources, *sources, name=self._name)

    def run(self, items: list[Item] | None = None) -> RunRecord:
        """Run the collected items (collecting first if needed)."""
        if not self._collected:
            self.collect()
        return run_items(self.session, items)


@contextlib.contextmanager
def scenario(
    *sources: Source,
    rootpath: pathlib.Path | None = None,
    spec: ConfigSpec | None = None,
    name: str = "scenario_module",
) -> Iterator[Scenario]:
    """Enter a nested config and running session for the given sources.

    Usage::

        with scenario(test_fn, SomeTestClass, rootpath=tmp_path) as s:
            items = s.collect()
            record = s.run()
        record.assert_outcomes(passed=2)
    """
    resolved = _resolve_spec(spec, rootpath)
    with configured(resolved) as config, running_session(config) as session:
        yield Scenario(config, session, sources, name)
