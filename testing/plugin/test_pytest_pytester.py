import py
from py._plugin.pytest_pytester import LineMatcher, LineComp

def test_reportrecorder(testdir):
    item = testdir.getitem("def test_func(): pass")
    recorder = testdir.getreportrecorder(item.config)
    assert not recorder.getfailures()
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
    py.test.raises(ValueError, "recorder.getfailures()")


def test_parseconfig(testdir):
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

