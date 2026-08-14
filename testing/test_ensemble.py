"""Tests for the experimental _pytest.ensemble API."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import ExitStack
import os
from pathlib import Path
import sys
import types
import unittest
import warnings

from _pytest._io import TerminalWriter
from _pytest.config import Config
from _pytest.config import ExitCode
from _pytest.config.exceptions import UsageError
from _pytest.config.findpaths import ConfigValue
from _pytest.ensemble import build_module
from _pytest.ensemble import collect_tests
from _pytest.ensemble import ConfigSpec
from _pytest.ensemble import configured
from _pytest.ensemble import Ensemble
from _pytest.ensemble import EnsembleModule
from _pytest.ensemble import run_tests
from _pytest.ensemble import running_session
from _pytest.nodes import Collector
from _pytest.pytester import Pytester
import pytest


class TestConfigSpec:
    def test_rootpath_required(self) -> None:
        with (
            pytest.raises(ValueError, match="rootpath is required"),
            ExitStack() as stack,
        ):
            stack.enter_context(configured(ConfigSpec()))

    def test_rootpath_must_be_dir(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="not a directory"), ExitStack() as stack:
            stack.enter_context(configured(ConfigSpec(rootpath=tmp_path / "missing")))

    def test_essential_plugins_validated(self, tmp_path: Path) -> None:
        with (
            pytest.raises(ValueError, match=r"essential plugins.*runner"),
            ExitStack() as stack,
        ):
            stack.enter_context(
                configured(ConfigSpec(rootpath=tmp_path, plugins=("python", "mark")))
            )

    def test_load_conftests_unsupported(self, tmp_path: Path) -> None:
        with pytest.raises(NotImplementedError, match="conftest"), ExitStack() as stack:
            stack.enter_context(
                configured(ConfigSpec(rootpath=tmp_path, load_conftests=True))
            )

    def test_configured_basics(self, tmp_path: Path) -> None:
        spec = ConfigSpec(rootpath=tmp_path, args=("-k", "nothing"))
        with configured(spec) as config:
            assert config.rootpath == tmp_path
            assert config.inipath is None
            assert config.args == []
            assert config.args_source is Config.ArgsSource.SPEC
            assert config.getoption("keyword") == "nothing"
            assert config.invocation_params.dir == tmp_path
        # paired teardown ran
        assert not config._configured

    def test_inicfg_is_authoritative(self, tmp_path: Path) -> None:
        spec = ConfigSpec(rootpath=tmp_path, inicfg={"usefixtures": ["myfix"]})
        with configured(spec) as config:
            assert config.getini("usefixtures") == ["myfix"]

    def test_excluded_plugins_absent(self, tmp_path: Path) -> None:
        with configured(ConfigSpec(rootpath=tmp_path)) as config:
            assert config.pluginmanager.get_plugin("capturemanager") is None
            assert config.pluginmanager.get_plugin("terminalreporter") is None
            assert not config.pluginmanager.hasplugin("capture")
            assert not config.pluginmanager.hasplugin("terminal")
            assert not config.pluginmanager.hasplugin("cacheprovider")

    def test_spec_derivation_helpers(self) -> None:
        spec = ConfigSpec()
        derived = spec.with_plugins("capture").without_plugins("unittest")
        assert "capture" in derived.plugins
        assert "unittest" not in derived.plugins
        # frozen: original unchanged
        assert "capture" not in spec.plugins

    @pytest.mark.parametrize(
        "spec_kwargs",
        [
            pytest.param({"args": ("--strict-markers",)}, id="override-ini-action"),
            pytest.param({"args": ("-o", "strict_markers=true")}, id="dash-o"),
            pytest.param(
                {"inicfg": {"addopts": "--strict-markers"}}, id="addopts-in-inicfg"
            ),
        ],
    )
    def test_ini_overrides_are_applied(
        self, tmp_path: Path, spec_kwargs: dict[str, object]
    ) -> None:
        """Options that override ini values must not be silently dropped."""
        with configured(ConfigSpec(rootpath=tmp_path, **spec_kwargs)) as config:  # type: ignore[arg-type]
            assert config.getini("strict_markers") is True

    def test_ini_overrides_are_not_invented(self, tmp_path: Path) -> None:
        with configured(ConfigSpec(rootpath=tmp_path)) as config:
            assert config.getini("strict_markers") is None

    def test_unregistered_marker_is_strict(self, tmp_path: Path) -> None:
        """The end the overrides serve: --strict-markers actually bites.

        Enforcement is asserted through ``-m`` expression validation rather
        than a ``@pytest.mark.unregistered`` decorator, because decorators in
        the enclosing test body are resolved against the *host* config at
        decoration time, long before the ensemble config exists.
        """

        def test_fn() -> None: ...

        spec = ConfigSpec(
            rootpath=tmp_path, args=("--strict-markers", "-m", "nowhere_registered")
        )
        with pytest.raises(UsageError, match="Unknown marker"):
            run_tests(test_fn, spec=spec)

    def test_unregistered_marker_allowed_without_strict(self, tmp_path: Path) -> None:
        def test_fn() -> None: ...

        spec = ConfigSpec(rootpath=tmp_path, args=("-m", "nowhere_registered"))
        run_tests(test_fn, spec=spec).assert_outcomes(deselected=1)

    def test_setup_plan_normalizes_options(self, tmp_path: Path) -> None:
        """--setup-plan implies --setup-only/--setup-show.

        The implication used to live in ``pytest_cmdline_main``, which an
        ensemble never reaches, so the flag was accepted and then ignored.
        """
        spec = ConfigSpec(rootpath=tmp_path, args=("--setup-plan",)).with_plugins(
            "setuponly", "setupplan"
        )
        with configured(spec) as config:
            assert config.getoption("setuponly") is True
            assert config.getoption("setupshow") is True

    def test_setup_plan_skips_the_call_phase(self, tmp_path: Path) -> None:
        ran = []

        def test_fn() -> None:
            ran.append(1)

        spec = ConfigSpec(rootpath=tmp_path, args=("--setup-plan",)).with_plugins(
            "setuponly", "setupplan"
        )
        record = run_tests(test_fn, spec=spec)
        assert ran == []
        assert record["test_fn"].call is None

    @pytest.mark.parametrize("wrap", [False, True], ids=["plain-list", "ConfigValue"])
    def test_spec_survives_reuse(self, tmp_path: Path, wrap: bool) -> None:
        """A frozen spec must not grow when it is configured repeatedly.

        ``addinivalue_line`` appends to the cached list, so handing the
        caller's own list to the config made every reuse accumulate.
        """
        value: object = ["mine: a marker"]
        if wrap:
            value = ConfigValue(value, origin="file", mode="ini")
        spec = ConfigSpec(rootpath=tmp_path, inicfg={"markers": value})

        seen = []
        for _ in range(3):
            with configured(spec) as config:
                seen.append(len(config.getini("markers")))
        stored = spec.inicfg["markers"]
        raw = stored.value if isinstance(stored, ConfigValue) else stored
        assert len(raw) == 1  # type: ignore[arg-type]
        assert len(set(seen)) == 1, f"config saw growing marker lists: {seen}"

    def test_assertion_explanation_is_the_ensemble_s(self, tmp_path: Path) -> None:
        """The failure explanation must be configured by the ensemble.

        ``assertion.util._reprcompare`` is process-global; without the
        assertion plugin it stays bound to whatever the host installed, so
        an explanation is still produced and the test goes green while
        silently reflecting the host's configuration.
        """
        seen: list[tuple[str, object, object]] = []

        class Comparer:
            def pytest_assertrepr_compare(
                self, op: str, left: object, right: object
            ) -> list[str]:
                seen.append((op, left, right))
                return ["ensemble-owned explanation"]

        def test_fails() -> None:
            # deliberately false, so the comparison hook has something to explain
            assert 1 == 2  # type: ignore[comparison-overlap]

        spec = ConfigSpec(rootpath=tmp_path, extra_plugins=(Comparer(),))
        record = run_tests(test_fails, spec=spec)
        record.assert_outcomes(failed=1)
        assert seen == [("==", 1, 2)]
        assert "ensemble-owned explanation" in record["test_fails"].call.longreprtext  # type: ignore[union-attr]

    def test_extra_plugin_by_name(self, tmp_path: Path) -> None:
        """String entries in extra_plugins are imported, objects registered."""
        spec = ConfigSpec(rootpath=tmp_path, extra_plugins=("_pytest.setuponly",))
        with configured(spec) as config:
            assert config.pluginmanager.get_plugin("_pytest.setuponly") is not None


class TestTerminalLessConfig:
    """A config without the terminal plugin still has to render sometimes."""

    def test_get_terminal_writer_falls_back(self, tmp_path: Path) -> None:
        with configured(ConfigSpec(rootpath=tmp_path)) as config:
            assert config.pluginmanager.get_plugin("terminalreporter") is None
            assert isinstance(config.get_terminal_writer(), TerminalWriter)

    def test_pdb_on_failure_does_not_crash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--pdb used to die reaching into a terminalreporter that is absent."""
        entered: list[object] = []

        def fake_post_mortem(tb_or_exc: object) -> None:
            entered.append(tb_or_exc)

        monkeypatch.setattr("_pytest.debugging.post_mortem", fake_post_mortem)

        def test_fails() -> None:
            raise AssertionError("boom")

        spec = ConfigSpec(rootpath=tmp_path, args=("--pdb",)).with_plugins("debugging")
        record = run_tests(test_fails, spec=spec)
        record.assert_outcomes(failed=1)
        assert len(entered) == 1


class TestCapturedOutput:
    def test_rendered_report_is_captured(self, tmp_path: Path) -> None:
        def test_ok() -> None: ...

        def test_bad() -> None:
            left = 1
            assert left == 2

        record = run_tests(test_ok, test_bad, rootpath=tmp_path, capture_output=True)
        record.assert_outcomes(passed=1, failed=1)
        record.stdout.fnmatch_lines(
            [
                "*test session starts*",
                "*FAILURES*",
                "*1 failed, 1 passed*",
            ]
        )
        # the structured view still agrees with the rendered one
        assert record["test_bad"].failed

    def test_output_never_reaches_the_outer_stdout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An ensemble must not be handed the stdout of whatever runs it."""

        class Tripwire:
            def write(self, text: str) -> int:
                raise AssertionError(f"ensemble wrote to the outer stdout: {text!r}")

            def flush(self) -> None: ...

            def isatty(self) -> bool:
                return False

        def test_ok() -> None: ...

        monkeypatch.setattr(sys, "stdout", Tripwire())
        record = run_tests(test_ok, rootpath=tmp_path, capture_output=True)
        assert "1 passed" in record.output

    def test_not_captured_by_default(self, tmp_path: Path) -> None:
        def test_ok() -> None: ...

        record = run_tests(test_ok, rootpath=tmp_path)
        assert record.output == ""
        assert record.stdout.lines == []


class TestRunLoop:
    def test_goes_through_pytest_runtestloop(self, tmp_path: Path) -> None:
        """Plugins wrapping the loop hook must see an ensemble run."""
        seen: list[str] = []

        class LoopWatcher:
            @pytest.hookimpl(wrapper=True)
            def pytest_runtestloop(
                self, session: object
            ) -> Generator[None, object, object]:
                seen.append("loop")
                return (yield)

        def test_ok() -> None: ...

        spec = ConfigSpec(rootpath=tmp_path, extra_plugins=(LoopWatcher(),))
        run_tests(test_ok, spec=spec).assert_outcomes(passed=1)
        assert seen == ["loop"]

    def test_progress_column_is_rendered(self, tmp_path: Path) -> None:
        """The terminal's deferred final fill needs the loop hook, and the
        progress column needs somewhere safe to write."""

        def test_a() -> None: ...

        def test_b() -> None: ...

        record = run_tests(test_a, test_b, rootpath=tmp_path, capture_output=True)
        record.stdout.fnmatch_lines(["*test_ensemble.py ..*[[]100%[]]*"])


class TestCollection:
    def test_collect_loose_functions(self, tmp_path: Path) -> None:
        def test_one() -> None: ...

        def test_two() -> None: ...

        items = collect_tests(test_one, test_two, rootpath=tmp_path)
        assert [item.nodeid for item in items] == [
            "test_ensemble.py::test_one",
            "test_ensemble.py::test_two",
        ]

    def test_collect_class(self, tmp_path: Path) -> None:
        class TestGroup:
            def test_method(self) -> None: ...

            @staticmethod
            def test_static() -> None: ...

        items = collect_tests(TestGroup, rootpath=tmp_path)
        assert [item.name for item in items] == ["test_method", "test_static"]
        assert items[0].nodeid == "test_ensemble.py::TestGroup::test_method"

    def test_collect_module_object(self, tmp_path: Path) -> None:
        def test_in_module() -> None: ...

        module = build_module("my_virtual", test_in_module)
        items = collect_tests(module, rootpath=tmp_path)
        assert [item.nodeid for item in items] == ["my_virtual.py::test_in_module"]

    def test_module_pytestmark_applies(self, tmp_path: Path) -> None:
        def test_marked() -> None: ...

        module = build_module(
            "marked_mod",
            test_marked,
            pytestmark=[pytest.mark.skip(reason="module-wide")],
        )
        record = run_tests(module, rootpath=tmp_path)
        record.assert_outcomes(skipped=1)

    def test_parametrize(self, tmp_path: Path) -> None:
        @pytest.mark.parametrize("x", [1, 2, 3])
        def test_param(x: int) -> None:
            assert x < 3

        items = collect_tests(test_param, rootpath=tmp_path)
        assert [item.name for item in items] == [
            "test_param[1]",
            "test_param[2]",
            "test_param[3]",
        ]
        record = run_tests(test_param, rootpath=tmp_path)
        record.assert_outcomes(passed=2, failed=1)

    def test_keyword_deselection(self, tmp_path: Path) -> None:
        def test_alpha() -> None: ...

        def test_beta() -> None: ...

        spec = ConfigSpec(rootpath=tmp_path, args=("-k", "alpha"))
        record = run_tests(test_alpha, test_beta, spec=spec)
        record.assert_outcomes(passed=1, deselected=1)

    def test_lowercase_class_not_collected(self, tmp_path: Path) -> None:
        class test:
            pass

        assert collect_tests(test, rootpath=tmp_path) == []

    def test_unittest_testcase(self, tmp_path: Path) -> None:
        class MyCase(unittest.TestCase):
            def test_method(self) -> None:
                self.assertEqual(1, 1)

        record = run_tests(MyCase, rootpath=tmp_path)
        record.assert_outcomes(passed=1)

    def test_two_module_sources(self, tmp_path: Path) -> None:
        def test_a() -> None: ...

        def test_b() -> None: ...

        mod_a = build_module("mod_a", test_a)
        mod_b = build_module("mod_b", test_b)
        items = collect_tests(mod_a, mod_b, rootpath=tmp_path)
        assert [item.nodeid for item in items] == [
            "mod_a.py::test_a",
            "mod_b.py::test_b",
        ]

    def test_build_module_requires_named_members(self) -> None:
        with pytest.raises(ValueError, match="has no __name__"):
            build_module("mod", 42)

    def test_collect_imported_tests_false_rejects_loose(self, tmp_path: Path) -> None:
        """Loose sources always live in a synthesized namespace, which
        collect_imported_tests=False would silently drop."""

        def test_loose() -> None: ...

        spec = ConfigSpec(rootpath=tmp_path, inicfg={"collect_imported_tests": "false"})
        with pytest.raises(ValueError, match="collect_imported_tests"):
            collect_tests(test_loose, spec=spec)


class TestRunning:
    def test_outcome_categories(self, tmp_path: Path) -> None:
        def test_passes() -> None: ...

        @pytest.mark.skipif("True", reason="nope")
        def test_skips() -> None: ...

        def test_fails() -> None:
            left = 1
            assert left == 2

        @pytest.mark.xfail(reason="known")
        def test_xfails() -> None:
            raise AssertionError("boom")

        record = run_tests(
            test_passes, test_skips, test_fails, test_xfails, rootpath=tmp_path
        )
        record.assert_outcomes(passed=1, skipped=1, failed=1, xfailed=1)
        assert record["test_passes"].passed
        assert record["test_fails"].failed
        assert record["test_skips"].skipped
        assert "nope" in record["test_skips"].setup.longreprtext  # type: ignore[union-attr]
        assert [r.when for r in record["test_passes"].reports] == [
            "setup",
            "call",
            "teardown",
        ]

    def test_setup_error_is_error(self, tmp_path: Path) -> None:
        @pytest.fixture
        def broken() -> None:
            raise RuntimeError("bad setup")

        def test_uses_broken(broken: None) -> None: ...

        record = run_tests(broken, test_uses_broken, rootpath=tmp_path)
        record.assert_outcomes(errors=1)
        assert record["test_uses_broken"].outcome == "error"

    def test_warning_recorded(self, tmp_path: Path) -> None:
        def test_warns() -> None:
            warnings.warn(UserWarning("boo"))

        # The host suite runs with filterwarnings=error, which is process
        # state the nested run inherits; the ensemble's own ini filters
        # take precedence over it.
        spec = ConfigSpec(rootpath=tmp_path, inicfg={"filterwarnings": ["always"]})
        record = run_tests(test_warns, spec=spec)
        record.assert_outcomes(passed=1, warnings=1)
        assert "boo" in str(record.warnings[0].message)

    def test_getitem_ambiguity(self, tmp_path: Path) -> None:
        def test_same() -> None: ...

        mod_a = build_module("dup_a", test_same)
        mod_b = build_module("dup_b", test_same)
        record = run_tests(mod_a, mod_b, rootpath=tmp_path)
        record.assert_outcomes(passed=2)
        assert record["dup_a.py::test_same"].passed
        with pytest.raises(KeyError, match="no unambiguous test"):
            record["test_same"]

    def test_stepwise_ensemble(self, tmp_path: Path) -> None:
        def test_one() -> None: ...

        with Ensemble(test_one, rootpath=tmp_path) as ensemble:
            items = ensemble.collect()
            assert len(items) == 1
            record = ensemble.run()
        record.assert_outcomes(passed=1)

    def test_sequential_ensembles(self, tmp_path: Path) -> None:
        def test_first() -> None: ...

        def test_second() -> None:
            assert False

        run_tests(test_first, rootpath=tmp_path).assert_outcomes(passed=1)
        run_tests(test_second, rootpath=tmp_path).assert_outcomes(failed=1)

    def test_run_subset_of_collected_items(self, tmp_path: Path) -> None:
        def test_a() -> None: ...

        def test_b() -> None: ...

        with Ensemble(test_a, test_b, rootpath=tmp_path) as ensemble:
            items = ensemble.collect()
            record = ensemble.run(items[:1])
        record.assert_outcomes(passed=1)
        assert list(record.by_test) == ["test_ensemble.py::test_a"]

    def test_configure_warnings_do_not_escape(self, tmp_path: Path) -> None:
        """An ensemble must not warn into whatever is running it.

        A host suite running with ``filterwarnings = error`` would fail a
        test for a warning that is not its own.
        """

        class WarnsAtConfigure:
            def pytest_configure(self, config: object) -> None:
                warnings.warn(UserWarning("from-the-ensemble"))

        def test_ok() -> None: ...

        spec = ConfigSpec(
            rootpath=tmp_path,
            extra_plugins=(WarnsAtConfigure(),),
            inicfg={"filterwarnings": ["always"]},
        )
        with warnings.catch_warnings(record=True) as escaped:
            warnings.simplefilter("always")
            record = run_tests(test_ok, spec=spec)

        assert [str(w.message) for w in escaped] == []
        assert "from-the-ensemble" in [str(w.message) for w in record.warnings]

    def test_session_teardown_is_in_the_record(self, tmp_path: Path) -> None:
        """A record built during the run predates pytest_sessionfinish.

        Plugins emit warnings from there, so a record that stopped at
        run() made assert_outcomes(warnings=...) quietly wrong.
        """

        class WarnsLate:
            def pytest_sessionfinish(self, session: object, exitstatus: object) -> None:
                warnings.warn(UserWarning("late"))

        def test_ok() -> None: ...

        spec = ConfigSpec(
            rootpath=tmp_path,
            extra_plugins=(WarnsLate(),),
            inicfg={"filterwarnings": ["always"]},
        )
        record = run_tests(test_ok, spec=spec)
        record.assert_outcomes(passed=1, warnings=1)
        assert [str(w.message) for w in record.warnings] == ["late"]

    def test_maxfail_stops_the_run(self, tmp_path: Path) -> None:
        """--maxfail/-x must not be silently inert.

        The early exit lives in pytest_runtestloop, which an ensemble does
        not go through, so without this the whole run proceeded and a test
        about stopping early would assert the opposite of its subject.
        """

        def test_a() -> None:
            raise AssertionError

        def test_b() -> None:
            raise AssertionError

        def test_c() -> None: ...

        spec = ConfigSpec(rootpath=tmp_path, args=("--maxfail=1",))
        record = run_tests(test_a, test_b, test_c, spec=spec)
        record.assert_outcomes(failed=1)
        assert list(record.by_test) == ["test_ensemble.py::test_a"]
        assert record.stopped == "stopping after 1 failures"

    def test_runs_to_the_end_without_maxfail(self, tmp_path: Path) -> None:
        def test_a() -> None:
            raise AssertionError

        def test_b() -> None: ...

        record = run_tests(test_a, test_b, rootpath=tmp_path)
        record.assert_outcomes(failed=1, passed=1)
        assert record.stopped is None

    def test_collection_error_counts_as_error(self, tmp_path: Path) -> None:
        @pytest.mark.parametrize("absent", [1])
        def test_bad() -> None: ...

        record = run_tests(test_bad, rootpath=tmp_path)
        record.assert_outcomes(errors=1)
        assert [r.nodeid for r in record.collect_errors] == ["test_ensemble.py"]

    def test_collect_tests_raises_on_collection_failure(self, tmp_path: Path) -> None:
        """An empty item list must not stand in for a collection failure."""

        @pytest.mark.parametrize("absent", [1])
        def test_bad() -> None: ...

        with pytest.raises(Collector.CollectError, match="uses no argument"):
            collect_tests(test_bad, rootpath=tmp_path)

    def test_collect_errors_reachable_stepwise(self, tmp_path: Path) -> None:
        """Ensemble.collect() stays permissive, but says what went wrong."""

        @pytest.mark.parametrize("absent", [1])
        def test_bad() -> None: ...

        with Ensemble(test_bad, rootpath=tmp_path) as ensemble:
            assert ensemble.collect() == []
            assert [r.nodeid for r in ensemble.collect_errors] == ["test_ensemble.py"]

    def test_no_collect_errors_when_nothing_matches(self, tmp_path: Path) -> None:
        """Genuinely collecting nothing is not an error."""

        class NotATest:
            pass

        assert collect_tests(NotATest, rootpath=tmp_path) == []

    def test_outcome_empty_when_no_call_phase(self, tmp_path: Path) -> None:
        """--setup-only produces setup/teardown reports whose status
        category is empty, so the item has no aggregate outcome."""

        def test_noop() -> None: ...

        spec = ConfigSpec(rootpath=tmp_path, args=("--setup-only",)).with_plugins(
            "setuponly"
        )
        record = run_tests(test_noop, spec=spec)
        assert record["test_noop"].outcome == ""


class TestEnsembleLifecycle:
    def test_rootpath_fills_in_spec(self, tmp_path: Path) -> None:
        """An explicit rootpath supplies a spec that does not carry one."""
        spec = ConfigSpec(args=("-k", "nothing"))
        with Ensemble(rootpath=tmp_path, spec=spec) as ensemble:
            assert ensemble.config.rootpath == tmp_path

    def test_not_reentrant(self, tmp_path: Path) -> None:
        ensemble = Ensemble(rootpath=tmp_path)
        with ensemble:
            with pytest.raises(RuntimeError, match="not reentrant"), ExitStack() as s:
                s.enter_context(ensemble)

    def test_failure_to_start_session_unconfigures(self, tmp_path: Path) -> None:
        """If the session fails to start, the already-configured config is
        still torn down."""

        class BoomPlugin:
            def pytest_sessionstart(self, session: object) -> None:
                raise RuntimeError("boom")

        plugin = BoomPlugin()
        spec = ConfigSpec(rootpath=tmp_path, extra_plugins=(plugin,))
        ensemble = Ensemble(spec=spec)
        with pytest.raises(RuntimeError, match="boom"), ExitStack() as stack:
            stack.enter_context(ensemble)

    def test_collect_is_idempotent(self, tmp_path: Path) -> None:
        """A second collect() must not register the same sources again."""

        def test_a() -> None: ...

        with Ensemble(test_a, rootpath=tmp_path) as ensemble:
            first = ensemble.collect()
            second = ensemble.collect()
            assert [i.nodeid for i in first] == [i.nodeid for i in second]
            ensemble.run().assert_outcomes(passed=1)

    def test_collect_accepts_extra_sources(self, tmp_path: Path) -> None:
        """Later rounds add to the tree without colliding with earlier ones."""

        def test_a() -> None: ...

        def test_b() -> None: ...

        with Ensemble(test_a, rootpath=tmp_path) as ensemble:
            ensemble.collect()
            ensemble.collect(test_b)
            assert [i.nodeid for i in ensemble.session.items] == [
                "test_ensemble.py::test_a",
                "test_ensemble_1.py::test_b",
            ]
            ensemble.run().assert_outcomes(passed=2)

    def test_exception_in_body_reaches_session_teardown(self, tmp_path: Path) -> None:
        """A failure inside the ensemble body is forwarded to the session
        teardown, not swallowed by closing the stack blind."""
        seen: list[int] = []

        class Recorder:
            def pytest_sessionfinish(self, exitstatus: int) -> None:
                seen.append(exitstatus)

        spec = ConfigSpec(rootpath=tmp_path, extra_plugins=(Recorder(),))
        with pytest.raises(RuntimeError, match="inner"):
            with Ensemble(spec=spec):
                raise RuntimeError("inner")
        assert seen == [ExitCode.INTERNAL_ERROR]


class TestFixtures:
    def test_function_fixture(self, tmp_path: Path) -> None:
        @pytest.fixture
        def value() -> int:
            return 41

        def test_uses_value(value: int) -> None:
            assert value == 41

        record = run_tests(value, test_uses_value, rootpath=tmp_path)
        record.assert_outcomes(passed=1)

    def test_class_scoped_fixture_and_teardown_order(self, tmp_path: Path) -> None:
        events: list[str] = []

        class TestGroup:
            @pytest.fixture(scope="class")
            def resource(self) -> Generator[str]:
                events.append("setup")
                yield "res"
                events.append("teardown")

            def test_one(self, resource: str) -> None:
                events.append("one")

            def test_two(self, resource: str) -> None:
                events.append("two")

        record = run_tests(TestGroup, rootpath=tmp_path)
        record.assert_outcomes(passed=2)
        assert events == ["setup", "one", "two", "teardown"]

    def test_module_scoped_fixture(self, tmp_path: Path) -> None:
        events: list[str] = []

        @pytest.fixture(scope="module")
        def modres() -> Generator[int]:
            events.append("setup")
            yield 1
            events.append("teardown")

        def test_a(modres: int) -> None:
            events.append("a")

        def test_b(modres: int) -> None:
            events.append("b")

        record = run_tests(modres, test_a, test_b, rootpath=tmp_path)
        record.assert_outcomes(passed=2)
        assert events == ["setup", "a", "b", "teardown"]

    def test_request_module_is_synthesized_module(self, tmp_path: Path) -> None:
        seen: list[types.ModuleType] = []

        def test_introspect(request: pytest.FixtureRequest) -> None:
            seen.append(request.module)

        run_tests(test_introspect, rootpath=tmp_path).assert_outcomes(passed=1)
        (module,) = seen
        assert isinstance(module, types.ModuleType)
        assert module.__name__ == "test_ensemble"

    def test_fixture_from_extra_plugin(self, tmp_path: Path) -> None:
        class FixturePlugin:
            @pytest.fixture
            def injected(self) -> str:
                return "from-plugin"

        def test_uses_injected(injected: str) -> None:
            assert injected == "from-plugin"

        spec = ConfigSpec(rootpath=tmp_path, extra_plugins=(FixturePlugin(),))
        run_tests(test_uses_injected, spec=spec).assert_outcomes(passed=1)

    def test_monkeypatch_fixture_available(self, tmp_path: Path) -> None:
        def test_uses_monkeypatch(monkeypatch: pytest.MonkeyPatch) -> None:
            monkeypatch.setenv("ENSEMBLE_PROBE", "1")
            assert os.environ["ENSEMBLE_PROBE"] == "1"

        run_tests(test_uses_monkeypatch, rootpath=tmp_path).assert_outcomes(passed=1)
        assert "ENSEMBLE_PROBE" not in os.environ


class TestNodeConstruction:
    def test_class_from_parent_keeps_obj(self, tmp_path: Path) -> None:
        """Class.from_parent(obj=...) takes precedence over name lookup."""

        class Hidden:
            def test_method(self) -> None: ...

        empty = build_module("holder")
        with configured(ConfigSpec(rootpath=tmp_path)) as config:
            with running_session(config) as session:
                module = EnsembleModule.from_parent(session, obj=empty, name="holder")
                cls = pytest.Class.from_parent(
                    module, name="NotAnAttribute", obj=Hidden
                )
                assert cls.obj is Hidden
                assert [item.name for item in cls.collect()] == ["test_method"]


class TestHermeticity:
    def test_no_process_state_leaked(self, tmp_path: Path) -> None:
        def test_noop() -> None: ...

        # Warm-up: let lazy imports happen before snapshotting.
        run_tests(test_noop, rootpath=tmp_path).assert_outcomes(passed=1)

        cwd = os.getcwd()
        sys_path = list(sys.path)
        modules = set(sys.modules)
        environ = dict(os.environ)

        run_tests(test_noop, rootpath=tmp_path).assert_outcomes(passed=1)

        assert os.getcwd() == cwd
        assert sys.path == sys_path
        assert set(sys.modules) == modules
        assert dict(os.environ) == environ

    def test_no_files_created(self, tmp_path: Path) -> None:
        def test_noop() -> None: ...

        run_tests(test_noop, rootpath=tmp_path).assert_outcomes(passed=1)
        assert list(tmp_path.iterdir()) == []


class TestPytesterInterplay:
    def test_ensemble_inside_full_pytest_run(self, pytester: Pytester) -> None:
        """The ensemble API works inside a captured, terminal-full pytest run."""
        pytester.makepyfile(
            """
            from _pytest.ensemble import run_tests

            def test_host(tmp_path):
                def test_inner():
                    assert 1 + 1 == 2

                record = run_tests(test_inner, rootpath=tmp_path)
                record.assert_outcomes(passed=1)
            """
        )
        result = pytester.runpytest_inprocess()
        result.assert_outcomes(passed=1)
