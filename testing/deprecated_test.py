# mypy: allow-untyped-defs
from __future__ import annotations

from _pytest import deprecated
from _pytest.pytester import Pytester
import pytest
from pytest import PytestDeprecationWarning


@pytest.mark.parametrize("plugin", sorted(deprecated.DEPRECATED_EXTERNAL_PLUGINS))
@pytest.mark.filterwarnings("default")
def test_external_plugins_integrated(pytester: Pytester, plugin) -> None:
    pytester.syspathinsert()
    pytester.makepyfile(**{plugin: ""})

    with pytest.warns(pytest.PytestConfigWarning):
        pytester.parseconfig("-p", plugin)


def test_hookspec_via_function_attributes_are_deprecated():
    from _pytest.config import PytestPluginManager

    pm = PytestPluginManager()

    class DeprecatedHookMarkerSpec:
        def pytest_bad_hook(self):
            pass

        pytest_bad_hook.historic = False  # type: ignore[attr-defined]

    with pytest.warns(
        PytestDeprecationWarning,
        match=r"Please use the pytest\.hookspec\(historic=False\) decorator",
    ) as recorder:
        pm.add_hookspecs(DeprecatedHookMarkerSpec)
    (record,) = recorder
    assert (
        record.lineno
        == DeprecatedHookMarkerSpec.pytest_bad_hook.__code__.co_firstlineno
    )
    assert record.filename == __file__


def test_hookimpl_via_function_attributes_are_deprecated():
    from _pytest.config import PytestPluginManager

    pm = PytestPluginManager()

    class DeprecatedMarkImplPlugin:
        def pytest_runtest_call(self):
            pass

        pytest_runtest_call.tryfirst = True  # type: ignore[attr-defined]

    with pytest.warns(
        PytestDeprecationWarning,
        match=r"Please use the pytest.hookimpl\(tryfirst=True\)",
    ) as recorder:
        pm.register(DeprecatedMarkImplPlugin())
    (record,) = recorder
    assert (
        record.lineno
        == DeprecatedMarkImplPlugin.pytest_runtest_call.__code__.co_firstlineno
    )
    assert record.filename == __file__


def test_yield_fixture_is_deprecated() -> None:
    with pytest.warns(DeprecationWarning, match=r"yield_fixture is deprecated"):

        @pytest.yield_fixture  # type: ignore[deprecated]
        def fix():
            assert False


def test_private_is_deprecated() -> None:
    class PrivateInit:
        def __init__(self, foo: int, *, _ispytest: bool = False) -> None:
            deprecated.check_ispytest(_ispytest)

    with pytest.warns(
        pytest.PytestDeprecationWarning, match="private pytest class or function"
    ):
        PrivateInit(10)

    # Doesn't warn.
    PrivateInit(10, _ispytest=True)


def test_class_scope_instance_method_is_deprecated(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        class TestClass:
            @pytest.fixture(scope="class")
            def fix(self):
                self.attr = True

            def test_foo(self, fix):
                pass
        """
    )
    result = pytester.runpytest("-Werror::pytest.PytestRemovedIn10Warning")
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        ["*PytestRemovedIn10Warning: Class-scoped fixture defined as instance method*"]
    )


def test_class_scope_classmethod_fixture_not_deprecated(pytester: Pytester) -> None:
    """A class-scoped fixture defined as @classmethod does NOT warn."""
    pytester.makepyfile(
        """
        import pytest

        class TestClass:
            @pytest.fixture(scope="class")
            @classmethod
            def fix(cls):
                cls.attr = True

            def test_foo(self, fix):
                assert type(self).attr is True
        """
    )
    result = pytester.runpytest("-Werror::pytest.PytestRemovedIn10Warning")
    result.assert_outcomes(passed=1)


class TestFixtureNodeidDeprecations:
    """Tests for deprecated baseid/nodeid string APIs in fixture registration.

    AI-generated coverage tests for legacy paths that will be removed in
    pytest 10. These exist solely to maintain patch coverage until the
    deprecated code is deleted.

    Legacy paths covered:
    - parsefactories(obj, nodeid_string) deprecation warning
    - parsefactories(obj, None) does NOT warn (standard plugin pattern)
    - parsefactories() with no args raises TypeError
    - _register_fixture(nodeid=string) deprecation warning
    - _nodeid_autousenames population and _getautousenames yield
    - _matchfactories string-based fallback (match + non-match branches)
    """

    def test_parsefactories_nodeid_deprecation(self, pytester: Pytester) -> None:
        """parsefactories(obj, "path") warns; parsefactories(obj, None) does not."""
        pytester.makeconftest(
            """
            import pytest
            import types
            import warnings

            def pytest_collection_modifyitems(session, items):
                fm = session._fixturemanager

                @pytest.fixture
                def fix_a():
                    return "a"

                @pytest.fixture
                def fix_b():
                    return "b"

                mod_with_path = types.ModuleType("plugin_path")
                mod_with_path.fix_a = fix_a
                mod_none = types.ModuleType("plugin_none")
                mod_none.fix_b = fix_b

                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    fm.parsefactories(mod_with_path, "some/nodeid")
                    fm.parsefactories(mod_none, None)

                nodeid_warns = [x for x in w if "parsefactories" in str(x.message)]
                assert len(nodeid_warns) == 2, f"Expected 2 warning, got: {w}"
            """
        )
        pytester.makepyfile(
            """
            def test_global_fix(fix_b):
                assert fix_b == "b"
            """
        )
        result = pytester.runpytest("-W", "default::pytest.PytestRemovedIn10Warning")
        result.assert_outcomes(passed=1)

    def test_parsefactories_no_args_raises_typeerror(self, pytester: Pytester) -> None:
        """parsefactories() with no holder and no node_or_obj raises TypeError."""
        pytester.makeconftest(
            """
            import pytest

            def pytest_collection_modifyitems(session, items):
                fm = session._fixturemanager
                with pytest.raises(TypeError, match="requires holder or node_or_obj"):
                    fm.parsefactories()
            """
        )
        pytester.makepyfile("def test_pass(): pass")
        result = pytester.runpytest()
        result.assert_outcomes(passed=1)

    def test_register_fixture_nodeid_and_autouse_legacy(
        self, pytester: Pytester
    ) -> None:
        """_register_fixture(nodeid=string) warns and autouse populates/yields.

        Covers end-to-end:
        - Deprecation warning on _register_fixture(nodeid=...)
        - _nodeid_autousenames populated for autouse + non-empty nodeid
        - _getautousenames yields from nodeid_basenames at lookup time
        """
        pytester.makeconftest(
            """
            import pytest
            import warnings

            _done = False

            def pytest_collectstart(collector):
                global _done
                if _done or not hasattr(collector.session, "_fixturemanager"):
                    return
                if collector.nodeid == "":
                    return
                _done = True
                fm = collector.session._fixturemanager
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    fm._register_fixture(
                        name="legacy_autouse",
                        func=lambda: None,
                        nodeid=collector.nodeid,
                        autouse=True,
                    )
                assert any("_register_fixture" in str(x.message) for x in w)
                assert "legacy_autouse" in fm._nodeid_autousenames[collector.nodeid]
            """
        )
        pytester.makepyfile(
            """
            def test_autouse_yielded(request):
                assert "legacy_autouse" in request.fixturenames
            """
        )
        result = pytester.runpytest("-W", "default::pytest.PytestRemovedIn10Warning")
        result.assert_outcomes(passed=1)

    def test_matchfactories_string_fallback(self, pytester: Pytester) -> None:
        """_matchfactories uses baseid string matching for legacy fixtures.

        Exercises both branches:
        - baseid="" matches all nodes (global fixture)
        - baseid="nonexistent/path" matches nothing (scoped fixture invisible)
        """
        pytester.makeconftest(
            """
            import pytest
            import warnings

            def pytest_collection_modifyitems(session, items):
                fm = session._fixturemanager
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    fm._register_fixture(
                        name="global_legacy", func=lambda: "ok", nodeid=""
                    )
                    fm._register_fixture(
                        name="scoped_legacy", func=lambda: "nope",
                        nodeid="nonexistent/path",
                    )
            """
        )
        pytester.makepyfile(
            """
            def test_global_visible(global_legacy):
                assert global_legacy == "ok"

            def test_scoped_invisible(request):
                defs = request.session._fixturemanager.getfixturedefs(
                    "scoped_legacy", request._pyfuncitem
                )
                assert defs == ()
            """
        )
        result = pytester.runpytest("-W", "ignore::pytest.PytestRemovedIn10Warning")
        result.assert_outcomes(passed=2)

    def test_fixturedef_has_location_deprecated(self, pytester: Pytester) -> None:
        """Accessing FixtureDef.has_location warns."""
        pytester.makepyfile(
            """
            import pytest

            @pytest.fixture
            def fix():
                return 1

            def test_it(request):
                fixturedef = request._fixturemanager.getfixturedefs(
                    "fix", request._pyfuncitem
                )[0]
                with pytest.warns(
                    pytest.PytestRemovedIn10Warning, match="has_location"
                ):
                    assert fixturedef.has_location is True
            """
        )
        result = pytester.runpytest()
        result.assert_outcomes(passed=1)


def test_callspec2_renamed() -> None:
    """Importing/accessing CallSpec2 warns and returns CallSpec."""
    import _pytest.python as python_mod
    from _pytest.python import CallSpec

    with pytest.warns(pytest.PytestRemovedIn10Warning, match="CallSpec2"):
        from _pytest.python import CallSpec2

    assert CallSpec2 is CallSpec

    with pytest.warns(pytest.PytestRemovedIn10Warning, match="CallSpec2"):
        assert python_mod.CallSpec2 is CallSpec
