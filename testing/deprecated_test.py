# mypy: allow-untyped-defs
from __future__ import annotations

import re

from _pytest import deprecated
from _pytest.compat import legacy_path
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

        @pytest.yield_fixture
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


def test_node_ctor_fspath_argument_is_deprecated(pytester: Pytester) -> None:
    mod = pytester.getmodulecol("")

    class MyFile(pytest.File):
        def collect(self):
            raise NotImplementedError()

    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match=re.escape(
            "The (fspath: py.path.local) argument to MyFile is deprecated."
        ),
    ):
        MyFile.from_parent(
            parent=mod.parent,
            fspath=legacy_path("bla"),
        )


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
