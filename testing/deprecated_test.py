from __future__ import absolute_import, division, print_function

import os

import pytest


@pytest.mark.filterwarnings("default")
def test_yield_tests_deprecation(testdir):
    testdir.makepyfile(
        """
        def func1(arg, arg2):
            assert arg == arg2
        def test_gen():
            yield "m1", func1, 15, 3*5
            yield "m2", func1, 42, 6*7
        def test_gen2():
            for k in range(10):
                yield func1, 1, 1
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*test_yield_tests_deprecation.py:3:*yield tests are deprecated*",
            "*test_yield_tests_deprecation.py:6:*yield tests are deprecated*",
            "*2 passed*",
        ]
    )
    assert result.stdout.str().count("yield tests are deprecated") == 2


@pytest.mark.filterwarnings("default")
def test_funcarg_prefix_deprecation(testdir):
    testdir.makepyfile(
        """
        def pytest_funcarg__value():
            return 10

        def test_funcarg_prefix(value):
            assert value == 10
    """
    )
    result = testdir.runpytest("-ra")
    result.stdout.fnmatch_lines(
        [
            (
                "*test_funcarg_prefix_deprecation.py:1: *pytest_funcarg__value: "
                'declaring fixtures using "pytest_funcarg__" prefix is deprecated*'
            ),
            "*1 passed*",
        ]
    )


@pytest.mark.filterwarnings("default")
def test_pytest_setup_cfg_deprecated(testdir):
    testdir.makefile(
        ".cfg",
        setup="""
        [pytest]
        addopts = --verbose
    """,
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        ["*pytest*section in setup.cfg files is deprecated*use*tool:pytest*instead*"]
    )


@pytest.mark.filterwarnings("default")
def test_pytest_custom_cfg_deprecated(testdir):
    testdir.makefile(
        ".cfg",
        custom="""
        [pytest]
        addopts = --verbose
    """,
    )
    result = testdir.runpytest("-c", "custom.cfg")
    result.stdout.fnmatch_lines(
        ["*pytest*section in custom.cfg files is deprecated*use*tool:pytest*instead*"]
    )


def test_str_args_deprecated(tmpdir):
    """Deprecate passing strings to pytest.main(). Scheduled for removal in pytest-4.0."""
    from _pytest.main import EXIT_NOTESTSCOLLECTED

    warnings = []

    class Collect(object):
        def pytest_warning_captured(self, warning_message):
            warnings.append(str(warning_message.message))

    ret = pytest.main("%s -x" % tmpdir, plugins=[Collect()])
    msg = (
        "passing a string to pytest.main() is deprecated, "
        "pass a list of arguments instead."
    )
    assert msg in warnings
    assert ret == EXIT_NOTESTSCOLLECTED


def test_getfuncargvalue_is_deprecated(request):
    pytest.deprecated_call(request.getfuncargvalue, "tmpdir")


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
            "*--result-log is deprecated and scheduled for removal in pytest 4.0*",
            "*See https://docs.pytest.org/en/latest/usage.html#creating-resultlog-format-files for more information*",
        ]
    )


@pytest.mark.filterwarnings("always:Metafunc.addcall is deprecated")
def test_metafunc_addcall_deprecated(testdir):
    testdir.makepyfile(
        """
        def pytest_generate_tests(metafunc):
            metafunc.addcall({'i': 1})
            metafunc.addcall({'i': 2})
        def test_func(i):
            pass
    """
    )
    res = testdir.runpytest("-s")
    assert res.ret == 0
    res.stdout.fnmatch_lines(
        ["*Metafunc.addcall is deprecated*", "*2 passed, 2 warnings*"]
    )


def test_terminal_reporter_writer_attr(pytestconfig):
    """Check that TerminalReporter._tw is also available as 'writer' (#2984)
    This attribute is planned to be deprecated in 3.4.
    """
    try:
        import xdist  # noqa

        pytest.skip("xdist workers disable the terminal reporter plugin")
    except ImportError:
        pass
    terminal_reporter = pytestconfig.pluginmanager.get_plugin("terminalreporter")
    assert terminal_reporter.writer is terminal_reporter._tw


@pytest.mark.parametrize("plugin", ["catchlog", "capturelog"])
def test_pytest_catchlog_deprecated(testdir, plugin):
    testdir.makepyfile(
        """
        def test_func(pytestconfig):
            pytestconfig.pluginmanager.register(None, 'pytest_{}')
    """.format(
            plugin
        )
    )
    res = testdir.runpytest()
    assert res.ret == 0
    res.stdout.fnmatch_lines(
        ["*pytest-*log plugin has been merged into the core*", "*1 passed, 1 warnings*"]
    )


def test_pytest_plugins_in_non_top_level_conftest_deprecated(testdir):
    from _pytest.deprecated import PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST

    subdirectory = testdir.tmpdir.join("subdirectory")
    subdirectory.mkdir()
    # create the inner conftest with makeconftest and then move it to the subdirectory
    testdir.makeconftest(
        """
        pytest_plugins=['capture']
    """
    )
    testdir.tmpdir.join("conftest.py").move(subdirectory.join("conftest.py"))
    # make the top level conftest
    testdir.makeconftest(
        """
        import warnings
        warnings.filterwarnings('always', category=DeprecationWarning)
    """
    )
    testdir.makepyfile(
        """
        def test_func():
            pass
    """
    )
    res = testdir.runpytest_subprocess()
    assert res.ret == 0
    msg = str(PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST).splitlines()[0]
    res.stdout.fnmatch_lines(
        "*subdirectory{sep}conftest.py:0: RemovedInPytest4Warning: {msg}*".format(
            sep=os.sep, msg=msg
        )
    )


def test_pytest_plugins_in_non_top_level_conftest_deprecated_no_top_level_conftest(
    testdir
):
    from _pytest.deprecated import PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST

    subdirectory = testdir.tmpdir.join("subdirectory")
    subdirectory.mkdir()
    testdir.makeconftest(
        """
        import warnings
        warnings.filterwarnings('always', category=DeprecationWarning)
        pytest_plugins=['capture']
    """
    )
    testdir.tmpdir.join("conftest.py").move(subdirectory.join("conftest.py"))

    testdir.makepyfile(
        """
        def test_func():
            pass
    """
    )

    res = testdir.runpytest_subprocess()
    assert res.ret == 0
    msg = str(PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST).splitlines()[0]
    res.stdout.fnmatch_lines(
        "*subdirectory{sep}conftest.py:0: RemovedInPytest4Warning: {msg}*".format(
            sep=os.sep, msg=msg
        )
    )


def test_pytest_plugins_in_non_top_level_conftest_deprecated_no_false_positives(
    testdir
):
    from _pytest.deprecated import PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST

    subdirectory = testdir.tmpdir.join("subdirectory")
    subdirectory.mkdir()
    testdir.makeconftest(
        """
        pass
    """
    )
    testdir.tmpdir.join("conftest.py").move(subdirectory.join("conftest.py"))

    testdir.makeconftest(
        """
        import warnings
        warnings.filterwarnings('always', category=DeprecationWarning)
        pytest_plugins=['capture']
    """
    )
    testdir.makepyfile(
        """
        def test_func():
            pass
    """
    )
    res = testdir.runpytest_subprocess()
    assert res.ret == 0
    msg = str(PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST).splitlines()[0]
    assert msg not in res.stdout.str()


def test_call_fixture_function_deprecated():
    """Check if a warning is raised if a fixture function is called directly (#3661)"""

    @pytest.fixture
    def fix():
        return 1

    with pytest.deprecated_call():
        assert fix() == 1


def test_pycollector_makeitem_is_deprecated():
    from _pytest.python import PyCollector
    from _pytest.warning_types import RemovedInPytest4Warning

    class PyCollectorMock(PyCollector):
        """evil hack"""

        def __init__(self):
            self.called = False

        def _makeitem(self, *k):
            """hack to disable the actual behaviour"""
            self.called = True

    collector = PyCollectorMock()
    with pytest.warns(RemovedInPytest4Warning):
        collector.makeitem("foo", "bar")
    assert collector.called
