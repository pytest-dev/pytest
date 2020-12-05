import re
import warnings
from unittest import mock

import pytest
from _pytest import deprecated
from _pytest.pytester import Pytester
from _pytest.pytester import Testdir


@pytest.mark.parametrize("attribute", pytest.collect.__all__)  # type: ignore
# false positive due to dynamic attribute
def test_pytest_collect_module_deprecated(attribute):
    with pytest.warns(DeprecationWarning, match=attribute):
        getattr(pytest.collect, attribute)


@pytest.mark.parametrize("plugin", sorted(deprecated.DEPRECATED_EXTERNAL_PLUGINS))
@pytest.mark.filterwarnings("default")
def test_external_plugins_integrated(testdir, plugin):
    testdir.syspathinsert()
    testdir.makepyfile(**{plugin: ""})

    with pytest.warns(pytest.PytestConfigWarning):
        testdir.parseconfig("-p", plugin)


def test_fillfuncargs_is_deprecated() -> None:
    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match=re.escape(
            "pytest._fillfuncargs() is deprecated, use "
            "function._request._fillfixtures() instead if you cannot avoid reaching into internals."
        ),
    ):
        pytest._fillfuncargs(mock.Mock())


def test_fillfixtures_is_deprecated() -> None:
    import _pytest.fixtures

    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match=re.escape(
            "_pytest.fixtures.fillfixtures() is deprecated, use "
            "function._request._fillfixtures() instead if you cannot avoid reaching into internals."
        ),
    ):
        _pytest.fixtures.fillfixtures(mock.Mock())


def test_minus_k_dash_is_deprecated(testdir) -> None:
    threepass = testdir.makepyfile(
        test_threepass="""
        def test_one(): assert 1
        def test_two(): assert 1
        def test_three(): assert 1
    """
    )
    result = testdir.runpytest("-k=-test_two", threepass)
    result.stdout.fnmatch_lines(["*The `-k '-expr'` syntax*deprecated*"])


def test_minus_k_colon_is_deprecated(testdir) -> None:
    threepass = testdir.makepyfile(
        test_threepass="""
        def test_one(): assert 1
        def test_two(): assert 1
        def test_three(): assert 1
    """
    )
    result = testdir.runpytest("-k", "test_two:", threepass)
    result.stdout.fnmatch_lines(["*The `-k 'expr:'` syntax*deprecated*"])


def test_fscollector_gethookproxy_isinitpath(testdir: Testdir) -> None:
    module = testdir.getmodulecol(
        """
        def test_foo(): pass
        """,
        withinit=True,
    )
    assert isinstance(module, pytest.Module)
    package = module.parent
    assert isinstance(package, pytest.Package)

    with pytest.warns(pytest.PytestDeprecationWarning, match="gethookproxy"):
        package.gethookproxy(testdir.tmpdir)

    with pytest.warns(pytest.PytestDeprecationWarning, match="isinitpath"):
        package.isinitpath(testdir.tmpdir)

    # The methods on Session are *not* deprecated.
    session = module.session
    with warnings.catch_warnings(record=True) as rec:
        session.gethookproxy(testdir.tmpdir)
        session.isinitpath(testdir.tmpdir)
    assert len(rec) == 0


def test_strict_option_is_deprecated(pytester: Pytester) -> None:
    """--strict is a deprecated alias to --strict-markers (#7530)."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.unknown
        def test_foo(): pass
        """
    )
    result = pytester.runpytest("--strict")
    result.stdout.fnmatch_lines(
        [
            "'unknown' not found in `markers` configuration option",
            "*PytestDeprecationWarning: The --strict option is deprecated, use --strict-markers instead.",
        ]
    )


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
