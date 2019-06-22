import sys

import pytest


def test_enabled(testdir):
    """Test single crashing test displays a traceback."""
    testdir.makepyfile(
        """
    import faulthandler
    def test_crash():
        faulthandler._sigabrt()
    """
    )
    result = testdir.runpytest_subprocess()
    result.stderr.fnmatch_lines(["*Fatal Python error*"])
    assert result.ret != 0


def test_crash_near_exit(testdir):
    """Test that fault handler displays crashes that happen even after
    pytest is exiting (for example, when the interpreter is shutting down).
    """
    testdir.makepyfile(
        """
    import faulthandler
    import atexit
    def test_ok():
        atexit.register(faulthandler._sigabrt)
    """
    )
    result = testdir.runpytest_subprocess()
    result.stderr.fnmatch_lines(["*Fatal Python error*"])
    assert result.ret != 0


def test_disabled(testdir):
    """Test option to disable fault handler in the command line.
    """
    testdir.makepyfile(
        """
    import faulthandler
    def test_disabled():
        assert not faulthandler.is_enabled()
    """
    )
    result = testdir.runpytest_subprocess("-p", "no:faulthandler")
    result.stdout.fnmatch_lines(["*1 passed*"])
    assert result.ret == 0


@pytest.mark.parametrize("enabled", [True, False])
def test_timeout(testdir, enabled):
    """Test option to dump tracebacks after a certain timeout.
    If faulthandler is disabled, no traceback will be dumped.
    """
    testdir.makepyfile(
        """
    import time
    def test_timeout():
        time.sleep(2.0)
    """
    )
    testdir.makeini(
        """
        [pytest]
        faulthandler_timeout = 1
        """
    )
    args = ["-p", "no:faulthandler"] if not enabled else []

    result = testdir.runpytest_subprocess(*args)
    tb_output = "most recent call first"
    if sys.version_info[:2] == (3, 3):
        tb_output = "Thread"
    if enabled:
        result.stderr.fnmatch_lines(["*%s*" % tb_output])
    else:
        assert tb_output not in result.stderr.str()
    result.stdout.fnmatch_lines(["*1 passed*"])
    assert result.ret == 0


@pytest.mark.parametrize("hook_name", ["pytest_enter_pdb", "pytest_exception_interact"])
def test_cancel_timeout_on_hook(monkeypatch, pytestconfig, hook_name):
    """Make sure that we are cancelling any scheduled traceback dumping due
    to timeout before entering pdb (pytest-dev/pytest-faulthandler#12) or any other interactive
    exception (pytest-dev/pytest-faulthandler#14).
    """
    import faulthandler
    from _pytest import faulthandler as plugin_module

    called = []

    monkeypatch.setattr(
        faulthandler, "cancel_dump_traceback_later", lambda: called.append(1)
    )

    # call our hook explicitly, we can trust that pytest will call the hook
    # for us at the appropriate moment
    hook_func = getattr(plugin_module, hook_name)
    hook_func()
    assert called == [1]
