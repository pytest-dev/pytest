""" log invocations of extension hooks to a file. """ 
import py

def pytest_addoption(parser):
    parser.addoption("--hooklog", dest="hooklog", default=None, 
        help="write hook calls to the given file.")

def pytest_configure(config):
    hooklog = config.getvalue("hooklog")
    if hooklog:
        assert not config.pluginmanager.comregistry.logfile
        config.pluginmanager.comregistry.logfile = open(hooklog, 'w')

def pytest_unconfigure(config):
    f = config.pluginmanager.comregistry.logfile
    if f:
        f.close()
        config.pluginmanager.comregistry.logfile = None

# ===============================================================================
# plugin tests 
# ===============================================================================

def test_functional(testdir):
    testdir.makepyfile("""
        def test_pass():
            pass
    """)
    testdir.runpytest("--hooklog=hook.log")
    s = testdir.tmpdir.join("hook.log").read()
    assert s.find("pytest_sessionstart") != -1
    assert s.find("ItemTestReport") != -1
    assert s.find("sessionfinish") != -1
