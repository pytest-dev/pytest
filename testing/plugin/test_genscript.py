import py, os, sys
import subprocess


def pytest_funcarg__standalone(request):
    return request.cached_setup(scope="module", setup=lambda: Standalone(request))

class Standalone:
    def __init__(self, request):
        self.testdir = request.getfuncargvalue("testdir")
        script = "mypytest"
        result = self.testdir.runpytest("--genscript=%s" % script)
        assert result.ret == 0
        self.script = self.testdir.tmpdir.join(script)
        assert self.script.check()

    def run(self, anypython, testdir, *args):
        testdir.chdir()
        return testdir._run(anypython, self.script, *args)

def test_gen(testdir, anypython, standalone):
    result = standalone.run(anypython, testdir, '--version')
    assert result.ret == 0
    result.stderr.fnmatch_lines([
        "*imported from*mypytest*"
    ])
    p = testdir.makepyfile("def test_func(): assert 0")
    result = standalone.run(anypython, testdir, p)
    assert result.ret != 0

def test_rundist(testdir, pytestconfig, standalone):
    pytestconfig.pluginmanager.skipifmissing("xdist")
    testdir.makepyfile("""
        def test_one():
            pass
    """)
    result = standalone.run(sys.executable, testdir, '-n', '3')
    assert result.ret == 0
    result.stdout.fnmatch_lines([
        "*1 passed*",
    ])
