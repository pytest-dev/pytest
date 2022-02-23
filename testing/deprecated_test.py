import re
import sys
import warnings
from pathlib import Path

import pytest
from _pytest import deprecated
from _pytest.compat import legacy_path
from _pytest.pytester import Pytester
from pytest import PytestDeprecationWarning


@pytest.mark.parametrize("plugin", sorted(deprecated.DEPRECATED_EXTERNAL_PLUGINS))
@pytest.mark.filterwarnings("default")
def test_external_plugins_integrated(pytester: Pytester, plugin) -> None:
    pytester.syspathinsert()
    pytester.makepyfile(**{plugin: ""})

    with pytest.warns(pytest.PytestConfigWarning):
        pytester.parseconfig("-p", plugin)


def test_fscollector_gethookproxy_isinitpath(pytester: Pytester) -> None:
    module = pytester.getmodulecol(
        """
        def test_foo(): pass
        """,
        withinit=True,
    )
    assert isinstance(module, pytest.Module)
    package = module.parent
    assert isinstance(package, pytest.Package)

    with pytest.warns(pytest.PytestDeprecationWarning, match="gethookproxy"):
        package.gethookproxy(pytester.path)

    with pytest.warns(pytest.PytestDeprecationWarning, match="isinitpath"):
        package.isinitpath(pytester.path)

    # The methods on Session are *not* deprecated.
    session = module.session
    with warnings.catch_warnings(record=True) as rec:
        session.gethookproxy(pytester.path)
        session.isinitpath(pytester.path)
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
            "*PytestRemovedIn8Warning: The --strict option is deprecated, use --strict-markers instead.",
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


@pytest.mark.parametrize("hooktype", ["hook", "ihook"])
def test_hookproxy_warnings_for_pathlib(tmp_path, hooktype, request):
    path = legacy_path(tmp_path)

    PATH_WARN_MATCH = r".*path: py\.path\.local\) argument is deprecated, please use \(collection_path: pathlib\.Path.*"
    if hooktype == "ihook":
        hooks = request.node.ihook
    else:
        hooks = request.config.hook

    with pytest.warns(PytestDeprecationWarning, match=PATH_WARN_MATCH) as r:
        l1 = sys._getframe().f_lineno
        hooks.pytest_ignore_collect(
            config=request.config, path=path, collection_path=tmp_path
        )
        l2 = sys._getframe().f_lineno

    (record,) = r
    assert record.filename == __file__
    assert l1 < record.lineno < l2

    hooks.pytest_ignore_collect(config=request.config, collection_path=tmp_path)

    # Passing entirely *different* paths is an outright error.
    with pytest.raises(ValueError, match=r"path.*fspath.*need to be equal"):
        with pytest.warns(PytestDeprecationWarning, match=PATH_WARN_MATCH) as r:
            hooks.pytest_ignore_collect(
                config=request.config, path=path, collection_path=Path("/bla/bla")
            )


def test_warns_none_is_deprecated():
    with pytest.warns(
        PytestDeprecationWarning,
        match=re.escape(
            "Passing None has been deprecated.\n"
            "See https://docs.pytest.org/en/latest/how-to/capture-warnings.html"
            "#additional-use-cases-of-warnings-in-tests"
            " for alternatives in common use cases."
        ),
    ):
        with pytest.warns(None):  # type: ignore[call-overload]
            pass


class TestSkipMsgArgumentDeprecated:
    def test_skip_with_msg_is_deprecated(self, pytester: Pytester) -> None:
        p = pytester.makepyfile(
            """
            import pytest

            def test_skipping_msg():
                pytest.skip(msg="skippedmsg")
            """
        )
        result = pytester.runpytest(p)
        result.stdout.fnmatch_lines(
            [
                "*PytestRemovedIn8Warning: pytest.skip(msg=...) is now deprecated, "
                "use pytest.skip(reason=...) instead",
                '*pytest.skip(msg="skippedmsg")*',
            ]
        )
        result.assert_outcomes(skipped=1, warnings=1)

    def test_fail_with_msg_is_deprecated(self, pytester: Pytester) -> None:
        p = pytester.makepyfile(
            """
            import pytest

            def test_failing_msg():
                pytest.fail(msg="failedmsg")
            """
        )
        result = pytester.runpytest(p)
        result.stdout.fnmatch_lines(
            [
                "*PytestRemovedIn8Warning: pytest.fail(msg=...) is now deprecated, "
                "use pytest.fail(reason=...) instead",
                '*pytest.fail(msg="failedmsg")',
            ]
        )
        result.assert_outcomes(failed=1, warnings=1)

    def test_exit_with_msg_is_deprecated(self, pytester: Pytester) -> None:
        p = pytester.makepyfile(
            """
            import pytest

            def test_exit_msg():
                pytest.exit(msg="exitmsg")
            """
        )
        result = pytester.runpytest(p)
        result.stdout.fnmatch_lines(
            [
                "*PytestRemovedIn8Warning: pytest.exit(msg=...) is now deprecated, "
                "use pytest.exit(reason=...) instead",
            ]
        )
        result.assert_outcomes(warnings=1)


def test_deprecation_of_cmdline_preparse(pytester: Pytester) -> None:
    pytester.makeconftest(
        """
        def pytest_cmdline_preparse(config, args):
            ...

        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*PytestRemovedIn8Warning: The pytest_cmdline_preparse hook is deprecated*",
            "*Please use pytest_load_initial_conftests hook instead.*",
        ]
    )


def test_node_ctor_fspath_argument_is_deprecated(pytester: Pytester) -> None:
    mod = pytester.getmodulecol("")

    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match=re.escape("The (fspath: py.path.local) argument to File is deprecated."),
    ):
        pytest.File.from_parent(
            parent=mod.parent,
            fspath=legacy_path("bla"),
        )


def test_importing_instance_is_deprecated(pytester: Pytester) -> None:
    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match=re.escape("The pytest.Instance collector type is deprecated"),
    ):
        pytest.Instance

    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match=re.escape("The pytest.Instance collector type is deprecated"),
    ):
        from _pytest.python import Instance  # noqa: F401
