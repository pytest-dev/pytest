"""
this little helper allows to run tests multiple times
in the same process.  useful for running tests from 
a console.  

NOTE: since 1.3.1 you can just call py.test.cmdline.main() 
multiple times - no special logic needed. 
"""
import py, sys

def pytest(argv=None):
    if argv is None:
        argv = []
    try:
        sys.argv[1:] = argv
        py.cmdline.pytest()
    except SystemExit:
        pass
    # we need to reset the global py.test.config object
    py.test.config = py.test.config.__class__()
