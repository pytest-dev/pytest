"""Nested configs and in-memory collection for pytest-under-pytest testing.

EXPERIMENTAL: internal API, no backwards-compatibility guarantees.

A pytest *ensemble* is a deliberately small pytest assembled from parts
handed to it, rather than a full session discovered from a filesystem: a
hermetic nested configuration built from declarative data
(:class:`ConfigSpec`), test items collected from in-memory python objects
instead of files on disk, run through the standard runtest protocol, with
typed report objects (:class:`RunRecord`) to assert on instead of
glob-matching rendered terminal output.

Known limitations (by design, for now):

* Ensembles never load conftest files; pass plugin objects via
  ``ConfigSpec.extra_plugins`` instead.
* The ``capture`` and ``terminal`` plugins are not loaded by default:
  ``capsys``/``capfd`` are unavailable inside an ensemble and no terminal
  output exists. Capture nesting is a planned follow-up.
* Assertion rewriting is not applied to ensemble sources; sources defined
  in the host test suite's own files are already rewritten by the host.
* Sources without real code objects (``exec``'d, lambdas) degrade
  ``reportinfo``/traceback quality.
* Process-global warning filters active around the ensemble (e.g. the
  host suite's ``filterwarnings = error``) are inherited; an ensemble's
  own ``inicfg={"filterwarnings": [...]}`` takes precedence over them.
"""

from __future__ import annotations

import contextlib
import pathlib
from typing import TYPE_CHECKING

from _pytest.config import Config
from _pytest.ensemble.collection import build_module
from _pytest.ensemble.collection import collect_sources
from _pytest.ensemble.collection import DEFAULT_MODULE_NAME
from _pytest.ensemble.collection import EnsembleModule
from _pytest.ensemble.collection import running_session
from _pytest.ensemble.collection import Source
from _pytest.ensemble.config import ConfigSpec
from _pytest.ensemble.config import configured
from _pytest.ensemble.config import DEFAULT_PLUGINS
from _pytest.ensemble.results import ItemRecord
from _pytest.ensemble.results import run_items
from _pytest.ensemble.results import RunRecord
from _pytest.main import Session
from _pytest.nodes import Item


if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self


__all__ = [
    "DEFAULT_MODULE_NAME",
    "DEFAULT_PLUGINS",
    "ConfigSpec",
    "Ensemble",
    "EnsembleModule",
    "ItemRecord",
    "RunRecord",
    "Source",
    "build_module",
    "collect_sources",
    "collect_tests",
    "configured",
    "run_items",
    "run_tests",
    "running_session",
]


def _resolve_spec(spec: ConfigSpec | None, rootpath: pathlib.Path | None) -> ConfigSpec:
    if spec is None:
        spec = ConfigSpec(rootpath=rootpath)
    elif rootpath is not None and spec.rootpath is None:
        spec = spec.replace(rootpath=rootpath)
    return spec


class Ensemble:
    """A nested config plus a running session, over which sources can be
    collected and run stepwise.

    Used as a context manager; the config is configured and the session
    started on enter, and both are torn down on exit::

        with Ensemble(test_fn, SomeTestClass, rootpath=tmp_path) as ensemble:
            items = ensemble.collect()
            record = ensemble.run()
        record.assert_outcomes(passed=2)

    For the common one-shot cases use :func:`run_tests` or
    :func:`collect_tests` instead.
    """

    #: The configured nested config; only available while entered.
    config: Config
    #: The started session; only available while entered.
    session: Session

    def __init__(
        self,
        *sources: Source,
        rootpath: pathlib.Path | None = None,
        spec: ConfigSpec | None = None,
        name: str = DEFAULT_MODULE_NAME,
    ) -> None:
        self._spec = _resolve_spec(spec, rootpath)
        self._sources = sources
        self._name = name
        self._collected = False
        self._stack: contextlib.ExitStack | None = None

    def __enter__(self) -> Self:
        if self._stack is not None:
            raise RuntimeError("Ensemble is not reentrant")
        stack = contextlib.ExitStack()
        try:
            self.config = stack.enter_context(configured(self._spec))
            self.session = stack.enter_context(running_session(self.config))
        except BaseException:
            stack.close()
            raise
        self._stack = stack
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._stack is not None, "Ensemble was not entered"
        stack, self._stack = self._stack, None
        # Forward the exception rather than closing blind, so the session
        # teardown sees that the body failed. Neither of the entered context
        # managers suppresses, so the result is not propagated.
        stack.__exit__(exc_type, exc, tb)

    def collect(self, *sources: Source) -> list[Item]:
        """Collect the ensemble's sources (plus any given extra ones)."""
        self._collected = True
        return collect_sources(self.session, *self._sources, *sources, name=self._name)

    def run(self, items: list[Item] | None = None) -> RunRecord:
        """Run the collected items (collecting first if needed)."""
        if not self._collected:
            self.collect()
        return run_items(self.session, items)


def run_tests(
    *sources: Source,
    rootpath: pathlib.Path | None = None,
    spec: ConfigSpec | None = None,
    name: str = DEFAULT_MODULE_NAME,
) -> RunRecord:
    """Collect and run the given in-memory sources in a nested config;
    return the structured results."""
    with Ensemble(*sources, rootpath=rootpath, spec=spec, name=name) as ensemble:
        return ensemble.run()


def collect_tests(
    *sources: Source,
    rootpath: pathlib.Path | None = None,
    spec: ConfigSpec | None = None,
    name: str = DEFAULT_MODULE_NAME,
) -> list[Item]:
    """Collect (only) the given in-memory sources; return the items.

    The nested config and session are torn down before returning; the
    items remain usable for structural assertions (names, nodeids, marks).
    """
    with Ensemble(*sources, rootpath=rootpath, spec=spec, name=name) as ensemble:
        return ensemble.collect()
