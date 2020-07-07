import copy
import inspect
from unittest import mock

import pytest
from _pytest import deprecated
from _pytest import nodes
from _pytest.config import Config


@pytest.mark.filterwarnings("default")
def test_resultlog_is_deprecated(testdir):
    result = testdir.runpytest("--help")
    result.stdout.fnmatch_lines(["*DEPRECATED path for machine-readable result log*"])

    testdir.makepyfile(
        """
        def test():
            pass
    """
    )
    result = testdir.runpytest("--result-log=%s" % testdir.tmpdir.join("result.log"))
    result.stdout.fnmatch_lines(
        [
            "*--result-log is deprecated, please try the new pytest-reportlog plugin.",
            "*See https://docs.pytest.org/en/stable/deprecations.html#result-log-result-log for more information*",
        ]
    )


@pytest.mark.parametrize("attribute", pytest.collect.__all__)  # type: ignore
# false positive due to dynamic attribute
def test_pytest_collect_module_deprecated(attribute):
    with pytest.warns(DeprecationWarning, match=attribute):
        getattr(pytest.collect, attribute)


def test_terminal_reporter_writer_attr(pytestconfig: Config) -> None:
    """Check that TerminalReporter._tw is also available as 'writer' (#2984)
    This attribute has been deprecated in 5.4.
    """
    try:
        import xdist  # noqa

        pytest.skip("xdist workers disable the terminal reporter plugin")
    except ImportError:
        pass
    terminal_reporter = pytestconfig.pluginmanager.get_plugin("terminalreporter")
    original_tw = terminal_reporter._tw

    with pytest.warns(pytest.PytestDeprecationWarning) as cw:
        assert terminal_reporter.writer is original_tw
    assert len(cw) == 1
    assert cw[0].filename == __file__

    new_tw = copy.copy(original_tw)
    with pytest.warns(pytest.PytestDeprecationWarning) as cw:
        terminal_reporter.writer = new_tw
        try:
            assert terminal_reporter._tw is new_tw
        finally:
            terminal_reporter.writer = original_tw
    assert len(cw) == 2
    assert cw[0].filename == cw[1].filename == __file__


@pytest.mark.parametrize("plugin", sorted(deprecated.DEPRECATED_EXTERNAL_PLUGINS))
@pytest.mark.filterwarnings("default")
def test_external_plugins_integrated(testdir, plugin):
    testdir.syspathinsert()
    testdir.makepyfile(**{plugin: ""})

    with pytest.warns(pytest.PytestConfigWarning):
        testdir.parseconfig("-p", plugin)


@pytest.mark.parametrize("junit_family", [None, "legacy", "xunit2"])
def test_warn_about_imminent_junit_family_default_change(testdir, junit_family):
    """Show a warning if junit_family is not defined and --junitxml is used (#6179)"""
    testdir.makepyfile(
        """
        def test_foo():
            pass
    """
    )
    if junit_family:
        testdir.makeini(
            """
            [pytest]
            junit_family={junit_family}
        """.format(
                junit_family=junit_family
            )
        )

    result = testdir.runpytest("--junit-xml=foo.xml")
    warning_msg = (
        "*PytestDeprecationWarning: The 'junit_family' default value will change*"
    )
    if junit_family:
        result.stdout.no_fnmatch_line(warning_msg)
    else:
        result.stdout.fnmatch_lines([warning_msg])


def test_node_direct_ctor_warning() -> None:
    class MockConfig:
        pass

    ms = MockConfig()
    with pytest.warns(
        DeprecationWarning,
        match="Direct construction of .* has been deprecated, please use .*.from_parent.*",
    ) as w:
        nodes.Node(name="test", config=ms, session=ms, nodeid="None")  # type: ignore
    assert w[0].lineno == inspect.currentframe().f_lineno - 1  # type: ignore
    assert w[0].filename == __file__


def test__fillfuncargs_is_deprecated() -> None:
    with pytest.warns(
        pytest.PytestDeprecationWarning,
        match="The `_fillfuncargs` function is deprecated",
    ):
        pytest._fillfuncargs(mock.Mock())


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
