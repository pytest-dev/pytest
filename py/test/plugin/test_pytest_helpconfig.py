import py, os

def test_version(testdir):
    assert py.version == py.__version__ 
    result = testdir.runpytest("--version")
    assert result.ret == 0
    p = py.path.local(py.__file__).dirpath()
    assert result.stderr.fnmatch_lines([
        '*py.test*%s*imported from*%s*' % (py.version, p)
    ])

def test_helpconfig(testdir):
    result = testdir.runpytest("--help-config")
    assert result.ret == 0
    assert result.stdout.fnmatch_lines([
        "*cmdline*conftest*ENV*",
    ])

