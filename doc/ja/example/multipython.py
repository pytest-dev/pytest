"""
module containing a parametrized tests testing cross-python
serialization via the pickle module.
"""
import py, pytest

pythonlist = ['python2.4', 'python2.5', 'python2.6', 'python2.7', 'python2.8']

def pytest_generate_tests(metafunc):
    # we parametrize all "python1" and "python2" arguments to iterate
    # over the python interpreters of our list above - the actual
    # setup and lookup of interpreters in the python1/python2 factories
    # respectively.
    for arg in metafunc.funcargnames:
        if arg in ("python1", "python2"):
            metafunc.parametrize(arg, pythonlist, indirect=True)

@pytest.mark.parametrize("obj", [42, {}, {1:3},])
def test_basic_objects(python1, python2, obj):
    python1.dumps(obj)
    python2.load_and_is_true("obj == %s" % obj)

def pytest_funcarg__python1(request):
    tmpdir = request.getfuncargvalue("tmpdir")
    picklefile = tmpdir.join("data.pickle")
    return Python(request.param, picklefile)

def pytest_funcarg__python2(request):
    python1 = request.getfuncargvalue("python1")
    return Python(request.param, python1.picklefile)

class Python:
    def __init__(self, version, picklefile):
        self.pythonpath = py.path.local.sysfind(version)
        if not self.pythonpath:
            py.test.skip("%r not found" %(version,))
        self.picklefile = picklefile
    def dumps(self, obj):
        dumpfile = self.picklefile.dirpath("dump.py")
        dumpfile.write(py.code.Source("""
            import pickle
            f = open(%r, 'wb')
            s = pickle.dump(%r, f)
            f.close()
        """ % (str(self.picklefile), obj)))
        py.process.cmdexec("%s %s" %(self.pythonpath, dumpfile))

    def load_and_is_true(self, expression):
        loadfile = self.picklefile.dirpath("load.py")
        loadfile.write(py.code.Source("""
            import pickle
            f = open(%r, 'rb')
            obj = pickle.load(f)
            f.close()
            res = eval(%r)
            if not res:
                raise SystemExit(1)
        """ % (str(self.picklefile), expression)))
        print (loadfile)
        py.process.cmdexec("%s %s" %(self.pythonpath, loadfile))
