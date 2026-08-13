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
  ``ConfigSpec.extra_plugins`` instead. A plugin object is equivalent to a
  conftest at the *rootdir*; nothing below rootdir is expressible, so
  per-directory conftest scoping has no analogue.
* **Capture does not nest.** ``capture`` is not loaded by default, and
  loading it via ``with_plugins("capture")`` registers a ``CaptureManager``
  without ever starting global capturing - ``pytest_load_initial_conftests``
  is where that happens, and an ensemble does not run it. Fixture-level
  ``capsys``/``capfd`` inside the ensemble therefore work, but output from
  the item itself is neither captured nor reported: **it escapes to the
  stdout of whatever is running the ensemble.** Starting global capturing
  here would redirect the process's streams underneath the host that is
  already capturing them; making that safe is the stack-aware
  ``CaptureManager`` work, not something this package can paper over.
* The ``terminal`` plugin is not loaded by default, so by default there is
  no rendered output at all. ``capture_output=True`` loads it bound to a
  private buffer, which is also what makes terminal-only options such as
  ``--tb``, ``-v`` and ``--color`` available. Note the progress column
  stays off regardless: the terminal reporter decides it from the
  ``capture`` option, which an ensemble does not have.
* Assertion *rewriting* is not applied to ensemble sources; sources defined
  in the host test suite's own files are already rewritten by the host. The
  assertion *explanation* is the ensemble's own, because the ``assertion``
  plugin is loaded by default - without it ``util._reprcompare`` would stay
  bound to the host's.
* Sources without real code objects (``exec``'d, lambdas) degrade
  ``reportinfo``/traceback quality. Items also report the *host* file as
  their location, so anything rendering ``file:line`` names the host.
* Process-global warning filters active around the ensemble (e.g. the
  host suite's ``filterwarnings = error``) are inherited; an ensemble's
  own ``inicfg={"filterwarnings": [...]}`` takes precedence over them.
  Warnings the ensemble itself raises do not escape: those from configure
  and unconfigure are captured and reported on :attr:`RunRecord.warnings`.
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
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
from _pytest.ensemble.results import ensure_recorder
from _pytest.ensemble.results import ItemRecord
from _pytest.ensemble.results import run_items
from _pytest.ensemble.results import RunRecord
from _pytest.main import Session
from _pytest.nodes import Collector
from _pytest.nodes import Item
from _pytest.reports import CollectReport


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
        capture_output: bool = False,
    ) -> None:
        self._spec = _resolve_spec(spec, rootpath)
        self._sources = sources
        self._name = name
        self._collected = False
        self._round = 0
        self._stack: contextlib.ExitStack | None = None
        self._sink: io.StringIO | None = None
        if capture_output:
            self._sink = io.StringIO()
            self._spec = self._spec.replace(output=self._sink)
            if "terminal" not in self._spec.plugins:
                self._spec = self._spec.with_plugins("terminal")

    @property
    def output(self) -> str:
        """What the terminal plugin has rendered so far, if capturing.

        Failure sections and the summary line are only written as the
        session finishes, so read this after leaving the context manager to
        get the whole report.
        """
        return self._sink.getvalue() if self._sink is not None else ""

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

    @property
    def collect_errors(self) -> list[CollectReport]:
        """The collect reports that failed, if any.

        Collection failures do not raise, so an ensemble that collects
        nothing because something blew up looks exactly like one that had
        nothing to collect; this is how the two are told apart.
        """
        recorder = ensure_recorder(self.config)
        return [report for report in recorder.collect_reports if report.failed]

    def collect(self, *sources: Source) -> list[Item]:
        """Collect the ensemble's sources (plus any given extra ones).

        Idempotent: calling it again without new sources returns the items
        already collected, rather than registering the same collectors a
        second time and reporting every test twice.
        """
        if self._collected:
            if not sources:
                return list(self.session.items)
            # Later rounds get their own synthesized module, so that loose
            # sources do not land on a module path already in the tree.
            self._round += 1
            return collect_sources(
                self.session, *sources, name=f"{self._name}_{self._round}"
            )
        self._collected = True
        return collect_sources(self.session, *self._sources, *sources, name=self._name)

    def run(self, items: list[Item] | None = None) -> RunRecord:
        """Run the collected items (collecting first if needed).

        Anything the session emits while tearing down - late warnings, the
        rendered summary - necessarily arrives after this returns; see
        :meth:`final_record`.
        """
        if not self._collected:
            self.collect()
        record = run_items(self.session, items)
        if self._sink is not None:
            record = dataclasses.replace(record, output=self.output)
        return record

    def final_record(self, record: RunRecord) -> RunRecord:
        """Refresh *record* with everything session teardown produced.

        ``pytest_sessionfinish`` runs as the ensemble is left, and plugins
        emit warnings (and the terminal writes its summary) from there.
        A record built during :meth:`run` predates all of it, which makes
        ``assert_outcomes(warnings=...)`` quietly wrong.
        """
        refreshed = RunRecord.from_recorder(
            ensure_recorder(self.config), config=self.config
        )
        return dataclasses.replace(
            refreshed, output=self.output, stopped=record.stopped
        )


def run_tests(
    *sources: Source,
    rootpath: pathlib.Path | None = None,
    spec: ConfigSpec | None = None,
    name: str = DEFAULT_MODULE_NAME,
    capture_output: bool = False,
) -> RunRecord:
    """Collect and run the given in-memory sources in a nested config;
    return the structured results.

    With ``capture_output``, the terminal plugin is loaded and what it
    renders is captured into :attr:`RunRecord.output` (and
    :attr:`RunRecord.stdout`) instead of reaching the real stdout.
    """
    ensemble = Ensemble(
        *sources,
        rootpath=rootpath,
        spec=spec,
        name=name,
        capture_output=capture_output,
    )
    with ensemble:
        record = ensemble.run()
    # Session teardown happens on the way out of the block, and it both
    # emits reports and warnings of its own and writes the failure sections
    # and summary line - so the complete picture only exists once the block
    # has been left.
    return ensemble.final_record(record)


def collect_tests(
    *sources: Source,
    rootpath: pathlib.Path | None = None,
    spec: ConfigSpec | None = None,
    name: str = DEFAULT_MODULE_NAME,
) -> list[Item]:
    """Collect (only) the given in-memory sources; return the items.

    The nested config and session are torn down before returning; the
    items remain usable for structural assertions (names, nodeids, marks).

    Raises :class:`~_pytest.nodes.Collector.CollectError` if collection
    failed: an empty list is otherwise indistinguishable from "collection
    blew up", which would quietly turn a "collects nothing" assertion into
    one that holds for the wrong reason. Use :class:`Ensemble` directly, or
    :func:`run_tests`, to inspect collection failures instead.
    """
    with Ensemble(*sources, rootpath=rootpath, spec=spec, name=name) as ensemble:
        items = ensemble.collect()
        if errors := ensemble.collect_errors:
            raise Collector.CollectError(
                "collection failed:\n"
                + "\n".join(f"{r.nodeid}: {r.longrepr}" for r in errors)
            )
        return items
