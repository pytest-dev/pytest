import inspect

import pytest
from _pytest import deprecated
from _pytest import nodes


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
            "*See https://docs.pytest.org/en/latest/deprecations.html#result-log-result-log for more information*",
        ]
    )


def test_terminal_reporter_writer_attr(pytestconfig):
    """Check that TerminalReporter._tw is also available as 'writer' (#2984)
    This attribute has been deprecated in 5.4.
    """
    try:
        import xdist  # noqa

        pytest.skip("xdist workers disable the terminal reporter plugin")
    except ImportError:
        pass
    terminal_reporter = pytestconfig.pluginmanager.get_plugin("terminalreporter")
    expected_tw = terminal_reporter._tw

    with pytest.warns(pytest.PytestDeprecationWarning):
        assert terminal_reporter.writer is expected_tw

    with pytest.warns(pytest.PytestDeprecationWarning):
        terminal_reporter.writer = expected_tw

    assert terminal_reporter._tw is expected_tw


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


def test_node_direct_ctor_warning():
    class MockConfig:
        pass

    ms = MockConfig()
    with pytest.warns(
        DeprecationWarning,
        match="direct construction of .* has been deprecated, please use .*.from_parent",
    ) as w:
        nodes.Node(name="test", config=ms, session=ms, nodeid="None")
    assert w[0].lineno == inspect.currentframe().f_lineno - 1
    assert w[0].filename == __file__


def assert_no_print_logs(testdir, args):
    result = testdir.runpytest(*args)
    result.stdout.fnmatch_lines(
        [
            "*--no-print-logs is deprecated and scheduled for removal in pytest 6.0*",
            "*Please use --show-capture instead.*",
        ]
    )


@pytest.mark.filterwarnings("default")
def test_noprintlogs_is_deprecated_cmdline(testdir):
    testdir.makepyfile(
        """
        def test_foo():
            pass
        """
    )

    assert_no_print_logs(testdir, ("--no-print-logs",))


@pytest.mark.filterwarnings("default")
def test_noprintlogs_is_deprecated_ini(testdir):
    testdir.makeini(
        """
        [pytest]
        log_print=False
        """
    )

    testdir.makepyfile(
        """
        def test_foo():
            pass
        """
    )

    assert_no_print_logs(testdir, ())
