# mypy: allow-untyped-defs
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


def test_fixture_disallow_on_marked_functions():
    """Test that applying @pytest.fixture to a marked function warns (#3364)."""
    with pytest.warns(
        pytest.PytestRemovedIn9Warning,
        match=r"Marks applied to fixtures have no effect",
    ) as record:

        @pytest.fixture
        @pytest.mark.parametrize("example", ["hello"])
        @pytest.mark.usefixtures("tmp_path")
        def foo():
            raise NotImplementedError()

    # it's only possible to get one warning here because you're already prevented
    # from applying @fixture twice
    # ValueError("fixture is being applied more than once to the same function")
    assert len(record) == 1


def test_fixture_disallow_marks_on_fixtures():
    """Test that applying a mark to a fixture warns (#3364)."""
    with pytest.warns(
        pytest.PytestRemovedIn9Warning,
        match=r"Marks applied to fixtures have no effect",
    ) as record:

        @pytest.mark.parametrize("example", ["hello"])
        @pytest.mark.usefixtures("tmp_path")
        @pytest.fixture
        def foo():
            raise NotImplementedError()

    assert len(record) == 2  # one for each mark decorator
    # should point to this file
    assert all(rec.filename == __file__ for rec in record)


def test_fixture_disallowed_between_marks():
    """Test that applying a mark to a fixture warns (#3364)."""
    with pytest.warns(
        pytest.PytestRemovedIn9Warning,
        match=r"Marks applied to fixtures have no effect",
    ) as record:

        @pytest.mark.parametrize("example", ["hello"])
        @pytest.fixture
        @pytest.mark.usefixtures("tmp_path")
        def foo():
            raise NotImplementedError()

    assert len(record) == 2  # one for each mark decorator
