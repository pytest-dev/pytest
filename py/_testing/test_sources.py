import os
import py


this_dir = py.path.local(__file__).dirpath()
_compile_checker = this_dir.join("check_compile.py")
_py_root = this_dir.join("..")
del this_dir

@py.test.mark.multi(pyversion=("2.4", "2.5", "2.6", "3.1"))
def test_syntax(pyversion):
    executable = py.path.local.sysfind("python" + pyversion)
    if executable is None:
        py.test.skip("no python%s found" % (pyversion,))
    for path, dirs, filenames in os.walk(str(_py_root)):
        for fn in filenames:
            if fn.endswith(".py"):
                full = os.path.join(path, fn)
                executable.sysexec(_compile_checker, full)
