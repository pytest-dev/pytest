"""Tests for the experimental _pytest.scenario API."""

from __future__ import annotations

from collections.abc import Generator
import os
from pathlib import Path
import sys
import types
import unittest
import warnings

from _pytest.config import Config
from _pytest.pytester import Pytester
from _pytest.scenario import collect_tests
from _pytest.scenario import ConfigSpec
from _pytest.scenario import configured
from _pytest.scenario import fake_module
from _pytest.scenario import run_tests
from _pytest.scenario import running_session
from _pytest.scenario import scenario
from _pytest.scenario import ScenarioModule
import pytest


class TestConfigSpec:
    def test_rootpath_required(self) -> None:
        with pytest.raises(ValueError, match="rootpath is required"):
            with configured(ConfigSpec()):
                pass

    def test_rootpath_must_be_dir(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="not a directory"):
            with configured(ConfigSpec(rootpath=tmp_path / "missing")):
                pass

    def test_essential_plugins_validated(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match=r"essential plugins.*runner"):
            with configured(ConfigSpec(rootpath=tmp_path, plugins=("python", "mark"))):
                pass

    def test_load_conftests_unsupported(self, tmp_path: Path) -> None:
        with pytest.raises(NotImplementedError, match="conftest"):
            with configured(ConfigSpec(rootpath=tmp_path, load_conftests=True)):
                pass

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


class TestCollection:
    def test_collect_loose_functions(self, tmp_path: Path) -> None:
        def test_one() -> None:
            pass

        def test_two() -> None:
            pass

        items = collect_tests(test_one, test_two, rootpath=tmp_path)
        assert [item.nodeid for item in items] == [
            "scenario_module.py::test_one",
            "scenario_module.py::test_two",
        ]

    def test_collect_class(self, tmp_path: Path) -> None:
        class TestGroup:
            def test_method(self) -> None:
                pass

            @staticmethod
            def test_static() -> None:
                pass

        items = collect_tests(TestGroup, rootpath=tmp_path)
        assert [item.name for item in items] == ["test_method", "test_static"]
        assert items[0].nodeid == "scenario_module.py::TestGroup::test_method"

    def test_collect_module_object(self, tmp_path: Path) -> None:
        def test_in_module() -> None:
            pass

        module = fake_module("my_virtual", test_in_module)
        items = collect_tests(module, rootpath=tmp_path)
        assert [item.nodeid for item in items] == ["my_virtual.py::test_in_module"]

    def test_module_pytestmark_applies(self, tmp_path: Path) -> None:
        def test_marked() -> None:
            pass

        module = fake_module(
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
        def test_alpha() -> None:
            pass

        def test_beta() -> None:
            pass

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
        def test_a() -> None:
            pass

        def test_b() -> None:
            pass

        mod_a = fake_module("mod_a", test_a)
        mod_b = fake_module("mod_b", test_b)
        items = collect_tests(mod_a, mod_b, rootpath=tmp_path)
        assert [item.nodeid for item in items] == [
            "mod_a.py::test_a",
            "mod_b.py::test_b",
        ]


class TestRunning:
    def test_outcome_categories(self, tmp_path: Path) -> None:
        def test_passes() -> None:
            pass

        @pytest.mark.skipif("True", reason="nope")
        def test_skips() -> None:
            pass

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

    def test_setup_error_is_error(self, tmp_path: Path) -> None:
        @pytest.fixture
        def broken() -> None:
            raise RuntimeError("bad setup")

        def test_uses_broken(broken: None) -> None:
            pass

        record = run_tests(broken, test_uses_broken, rootpath=tmp_path)
        record.assert_outcomes(errors=1)
        assert record["test_uses_broken"].outcome == "error"

    def test_warning_recorded(self, tmp_path: Path) -> None:
        def test_warns() -> None:
            warnings.warn(UserWarning("boo"))

        # The host suite runs with filterwarnings=error, which is process
        # state the nested run inherits; the scenario's own ini filters
        # take precedence over it.
        spec = ConfigSpec(rootpath=tmp_path, inicfg={"filterwarnings": ["always"]})
        record = run_tests(test_warns, spec=spec)
        record.assert_outcomes(passed=1, warnings=1)
        assert "boo" in str(record.warnings[0].message)

    def test_getitem_ambiguity(self, tmp_path: Path) -> None:
        def test_same() -> None:
            pass

        mod_a = fake_module("dup_a", test_same)
        mod_b = fake_module("dup_b", test_same)
        record = run_tests(mod_a, mod_b, rootpath=tmp_path)
        record.assert_outcomes(passed=2)
        assert record["dup_a.py::test_same"].passed
        with pytest.raises(KeyError, match="no unambiguous test"):
            record["test_same"]

    def test_stepwise_scenario(self, tmp_path: Path) -> None:
        def test_one() -> None:
            pass

        with scenario(test_one, rootpath=tmp_path) as s:
            items = s.collect()
            assert len(items) == 1
            record = s.run()
        record.assert_outcomes(passed=1)

    def test_sequential_scenarios(self, tmp_path: Path) -> None:
        def test_first() -> None:
            pass

        def test_second() -> None:
            assert False

        run_tests(test_first, rootpath=tmp_path).assert_outcomes(passed=1)
        run_tests(test_second, rootpath=tmp_path).assert_outcomes(failed=1)


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
        assert module.__name__ == "scenario_module"

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
            monkeypatch.setenv("SCENARIO_PROBE", "1")
            assert os.environ["SCENARIO_PROBE"] == "1"

        run_tests(test_uses_monkeypatch, rootpath=tmp_path).assert_outcomes(passed=1)
        assert "SCENARIO_PROBE" not in os.environ


class TestNodeConstruction:
    def test_class_from_parent_keeps_obj(self, tmp_path: Path) -> None:
        """Class.from_parent(obj=...) takes precedence over name lookup."""

        class Hidden:
            def test_method(self) -> None:
                pass

        empty = fake_module("holder")
        with configured(ConfigSpec(rootpath=tmp_path)) as config:
            with running_session(config) as session:
                module = ScenarioModule.from_parent(session, obj=empty, name="holder")
                cls = pytest.Class.from_parent(
                    module, name="NotAnAttribute", obj=Hidden
                )
                assert cls.obj is Hidden
                assert [item.name for item in cls.collect()] == ["test_method"]


class TestHermeticity:
    def test_no_process_state_leaked(self, tmp_path: Path) -> None:
        def test_noop() -> None:
            pass

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
        def test_noop() -> None:
            pass

        run_tests(test_noop, rootpath=tmp_path).assert_outcomes(passed=1)
        assert list(tmp_path.iterdir()) == []


class TestPytesterInterplay:
    def test_scenario_inside_full_pytest_run(self, pytester: Pytester) -> None:
        """The scenario API works inside a captured, terminal-full pytest run."""
        pytester.makepyfile(
            """
            from _pytest.scenario import run_tests

            def test_host(tmp_path):
                def test_inner():
                    assert 1 + 1 == 2

                record = run_tests(test_inner, rootpath=tmp_path)
                record.assert_outcomes(passed=1)
            """
        )
        result = pytester.runpytest_inprocess()
        result.assert_outcomes(passed=1)
