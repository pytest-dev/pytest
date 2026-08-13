"""Structured results for ensemble runs (EXPERIMENTAL)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
import dataclasses
import warnings as warnings_module

from _pytest.config import Config
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import CollectReport
from _pytest.reports import TestReport


class RunRecorder:
    """Plugin recording reports/warnings/deselections on an ensemble config."""

    name = "ensemble-recorder"

    def __init__(self) -> None:
        self.test_reports: list[TestReport] = []
        self.collect_reports: list[CollectReport] = []
        self.warnings: list[warnings_module.WarningMessage] = []
        self.deselected: int = 0

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        self.test_reports.append(report)

    def pytest_collectreport(self, report: CollectReport) -> None:
        self.collect_reports.append(report)

    def pytest_warning_recorded(
        self, warning_message: warnings_module.WarningMessage
    ) -> None:
        self.warnings.append(warning_message)

    def pytest_deselected(self, items: Sequence[Item]) -> None:
        self.deselected += len(items)


def ensure_recorder(config: Config) -> RunRecorder:
    """Get the recorder registered on the config, installing it if needed."""
    recorder: RunRecorder | None = config.pluginmanager.get_plugin(RunRecorder.name)
    if recorder is None:
        recorder = RunRecorder()
        config.pluginmanager.register(recorder, RunRecorder.name)
    return recorder


@dataclasses.dataclass(frozen=True)
class ItemRecord:
    """The reports of one test item's run, by phase."""

    nodeid: str
    setup: TestReport | None
    call: TestReport | None
    teardown: TestReport | None
    #: Aggregate category as reported by ``pytest_report_teststatus``
    #: ("passed", "failed", "skipped", "error", "xfailed", "xpassed", ...).
    outcome: str

    @property
    def reports(self) -> list[TestReport]:
        return [r for r in (self.setup, self.call, self.teardown) if r is not None]

    @property
    def passed(self) -> bool:
        return self.outcome == "passed"

    @property
    def failed(self) -> bool:
        return self.outcome in ("failed", "error")

    @property
    def skipped(self) -> bool:
        return self.outcome == "skipped"


@dataclasses.dataclass(frozen=True)
class RunRecord:
    """Typed, structured results of an ensemble run.

    Everything is derived from real report objects — nothing is scraped
    from rendered output.
    """

    reports: list[TestReport]
    collect_reports: list[CollectReport]
    warnings: list[warnings_module.WarningMessage]
    deselected: int
    by_test: dict[str, ItemRecord]
    _by_name: dict[str, ItemRecord]
    _counts: dict[str, int]

    @classmethod
    def from_recorder(cls, recorder: RunRecorder, *, config: Config) -> RunRecord:
        counts: Counter[str] = Counter()
        phases: dict[str, dict[str, TestReport]] = {}
        categories: dict[str, list[str]] = {}
        for report in recorder.test_reports:
            phases.setdefault(report.nodeid, {})[report.when] = report
            status = config.hook.pytest_report_teststatus(report=report, config=config)
            if status is not None:
                category = status[0]
            else:
                # The catch-all status impl lives in the terminal plugin,
                # which ensemble configs exclude; mirror its categorization.
                category = report.outcome
            if category:
                counts[category] += 1
                categories.setdefault(report.nodeid, []).append(category)
        for collect_report in recorder.collect_reports:
            if collect_report.failed:
                counts["error"] += 1

        by_test: dict[str, ItemRecord] = {}
        for nodeid, by_when in phases.items():
            cats = categories.get(nodeid, [])
            if "error" in cats:
                outcome = "error"
            elif cats:
                outcome = cats[-1]
            else:
                outcome = ""
            by_test[nodeid] = ItemRecord(
                nodeid=nodeid,
                setup=by_when.get("setup"),
                call=by_when.get("call"),
                teardown=by_when.get("teardown"),
                outcome=outcome,
            )

        name_map: dict[str, ItemRecord | None] = {}
        for nodeid, record in by_test.items():
            name = nodeid.rpartition("::")[2]
            # Ambiguous bare names are poisoned rather than guessed.
            name_map[name] = None if name in name_map else record
        by_name = {name: rec for name, rec in name_map.items() if rec is not None}

        return cls(
            reports=list(recorder.test_reports),
            collect_reports=list(recorder.collect_reports),
            warnings=list(recorder.warnings),
            deselected=recorder.deselected,
            by_test=by_test,
            _by_name=by_name,
            _counts=dict(counts),
        )

    def __getitem__(self, name: str) -> ItemRecord:
        if name in self.by_test:
            return self.by_test[name]
        if name in self._by_name:
            return self._by_name[name]
        raise KeyError(
            f"no unambiguous test named {name!r}; known: {sorted(self.by_test)}"
        )

    def outcomes(self) -> dict[str, int]:
        """Outcome category counts, keyed like the terminal summary
        ("passed", "failed", "errors", "skipped", "xfailed", "xpassed")."""
        counts = dict(self._counts)
        if "error" in counts:
            counts["errors"] = counts.pop("error")
        return counts

    def assert_outcomes(
        self,
        *,
        passed: int = 0,
        skipped: int = 0,
        failed: int = 0,
        errors: int = 0,
        xpassed: int = 0,
        xfailed: int = 0,
        warnings: int | None = None,
        deselected: int | None = None,
    ) -> None:
        """Assert the run produced exactly the given outcome counts.

        Signature-compatible with :meth:`RunResult.assert_outcomes
        <_pytest.pytester.RunResult.assert_outcomes>`.
        """
        __tracebackhide__ = True
        from _pytest.pytester_assertions import assert_outcomes

        outcomes = self.outcomes()
        outcomes["warnings"] = len(self.warnings)
        outcomes["deselected"] = self.deselected
        assert_outcomes(
            outcomes,
            passed=passed,
            skipped=skipped,
            failed=failed,
            errors=errors,
            xpassed=xpassed,
            xfailed=xfailed,
            warnings=warnings,
            deselected=deselected,
        )


def run_items(session: Session, items: Sequence[Item] | None = None) -> RunRecord:
    """Run items through the standard runtest protocol hook and return
    the structured results recorded so far on this config."""
    if items is None:
        items = list(session.items)
    recorder = ensure_recorder(session.config)
    for i, item in enumerate(items):
        nextitem = items[i + 1] if i + 1 < len(items) else None
        item.ihook.pytest_runtest_protocol(item=item, nextitem=nextitem)
    return RunRecord.from_recorder(recorder, config=session.config)
