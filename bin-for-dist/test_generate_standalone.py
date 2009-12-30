import py, os, sys
import generate_standalone_pytest
import subprocess
mydir = py.path.local(__file__).dirpath()
pybasedir = mydir.join("..")
assert pybasedir.join("py").check()

def pytest_funcarg__standalone(request):
    return request.cached_setup(scope="module", setup=lambda: Standalone(request))

class Standalone:
    def __init__(self, request):
        self.testdir = request.getfuncargvalue("testdir")
        infile = mydir.join("py.test-in")
        self.script = self.testdir.tmpdir.join("mypytest")
        generate_standalone_pytest.main(pybasedir=pybasedir,
            infile=infile, outfile=self.script)

    def run(self, anypython, testdir, *args):
        testdir.chdir()
        return testdir._run(anypython, self.script, *args)

def test_gen(testdir, anypython, standalone):
    result = standalone.run(anypython, testdir, '-h')
    assert result.ret == 0
    result = standalone.run(anypython, testdir, '--version')
    assert result.ret == 0
    result.stderr.fnmatch_lines([
        "*imported from*mypytest"
    ])

def test_rundist(testdir, standalone):
    testdir.makepyfile("""
        def test_one():
            pass
    """)
    result = standalone.run(sys.executable, testdir, '-n', '3')
    assert result.ret == 0
    result.stdout.fnmatch_lines([
        "*1 passed*"
    ])
