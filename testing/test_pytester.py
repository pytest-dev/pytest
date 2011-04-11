import py
import pytest
import os, sys
from _pytest.pytester import LineMatcher, LineComp, HookRecorder
from _pytest.core import PluginManager

def test_reportrecorder(testdir):
    item = testdir.getitem("def test_func(): pass")
    recorder = testdir.getreportrecorder(item.config)
    assert not recorder.getfailures()

    pytest.xfail("internal reportrecorder tests need refactoring")
    class rep:
        excinfo = None
        passed = False
        failed = True
        skipped = False
        when = "call"

    recorder.hook.pytest_runtest_logreport(report=rep)
    failures = recorder.getfailures()
    assert failures == [rep]
    failures = recorder.getfailures()
    assert failures == [rep]

    class rep:
        excinfo = None
        passed = False
        failed = False
        skipped = True
        when = "call"
    rep.passed = False
    rep.skipped = True
    recorder.hook.pytest_runtest_logreport(report=rep)

    modcol = testdir.getmodulecol("")
    rep = modcol.config.hook.pytest_make_collect_report(collector=modcol)
    rep.passed = False
    rep.failed = True
    rep.skipped = False
    recorder.hook.pytest_collectreport(report=rep)

    passed, skipped, failed = recorder.listoutcomes()
    assert not passed and skipped and failed

    numpassed, numskipped, numfailed = recorder.countoutcomes()
    assert numpassed == 0
    assert numskipped == 1
    assert numfailed == 1
    assert len(recorder.getfailedcollections()) == 1

    recorder.unregister()
    recorder.clear()
    recorder.hook.pytest_runtest_logreport(report=rep)
    pytest.raises(ValueError, "recorder.getfailures()")


def test_parseconfig(testdir):
    import py
    config1 = testdir.parseconfig()
    config2 = testdir.parseconfig()
    assert config2 != config1
    assert config1 != py.test.config

def test_testdir_runs_with_plugin(testdir):
    testdir.makepyfile("""
        pytest_plugins = "pytest_pytester"
        def test_hello(testdir):
            assert 1
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        "*1 passed*"
    ])

def test_hookrecorder_basic():
    rec = HookRecorder(PluginManager())
    class ApiClass:
        def pytest_xyz(self, arg):
            "x"
    rec.start_recording(ApiClass)
    rec.hook.pytest_xyz(arg=123)
    call = rec.popcall("pytest_xyz")
    assert call.arg == 123
    assert call._name == "pytest_xyz"
    pytest.raises(pytest.fail.Exception, "rec.popcall('abc')")

def test_hookrecorder_basic_no_args_hook():
    rec = HookRecorder(PluginManager())
    apimod = type(os)('api')
    def pytest_xyz():
        "x"
    apimod.pytest_xyz = pytest_xyz
    rec.start_recording(apimod)
    rec.hook.pytest_xyz()
    call = rec.popcall("pytest_xyz")
    assert call._name == "pytest_xyz"

def test_functional(testdir, linecomp):
    reprec = testdir.inline_runsource("""
        import pytest
        from _pytest.core import HookRelay, PluginManager
        pytest_plugins="pytester"
        def test_func(_pytest):
            class ApiClass:
                def pytest_xyz(self, arg):  "x"
            hook = HookRelay([ApiClass], PluginManager(load=False))
            rec = _pytest.gethookrecorder(hook)
            class Plugin:
                def pytest_xyz(self, arg):
                    return arg + 1
            rec._pluginmanager.register(Plugin())
            res = rec.hook.pytest_xyz(arg=41)
            assert res == [42]
    """)
    reprec.assertoutcome(passed=1)


def test_makepyfile_unicode(testdir):
    global unichr
    try:
        unichr(65)
    except NameError:
        unichr = chr
    testdir.makepyfile(unichr(0xfffd))
