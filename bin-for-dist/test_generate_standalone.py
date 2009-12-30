import py, os
import generate_standalone_pytest
import subprocess
mydir = py.path.local(__file__).dirpath()

def test_gen(testdir, anypython):
    testdir.chdir() 
    infile = mydir.join("py.test-in")
    outfile = testdir.tmpdir.join("mypytest")
    generate_standalone_pytest.main(pydir=os.path.dirname(py.__file__),
        infile=infile, outfile=outfile)
    result = testdir._run(anypython, outfile, '-h')
    assert result.ret == 0
    result = testdir._run(anypython, outfile, '--version')
    assert result.ret == 0
    result.stderr.fnmatch_lines([
        "*imported from*mypytest"
    ])
