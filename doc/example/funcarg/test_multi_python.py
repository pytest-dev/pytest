"""

module containing a parametrized tests testing cross-python
serialization via the pickle module. 
"""
import py

pythonlist = ['python2.3', 'python2.4', 'python2.5', 'python2.6'] 
# 'jython' 'python3.1']
  
def pytest_generate_tests(metafunc):
    if 'python1' in metafunc.funcargnames:
        assert 'python2' in metafunc.funcargnames
        for obj in metafunc.function.multiarg.kwargs['obj']:
            for py1 in pythonlist:
                for py2 in pythonlist:
                    metafunc.addcall(id="%s-%s-%s" % (py1, py2, obj), 
                        param=(py1, py2, obj))
        
@py.test.mark.multiarg(obj=[42, {}, {1:3},])
def test_basic_objects(python1, python2, obj):
    python1.dumps(obj)
    python2.load_and_is_true("obj == %s" % obj)

def pytest_funcarg__python1(request):
    tmpdir = request.getfuncargvalue("tmpdir")
    picklefile = tmpdir.join("data.pickle")
    return Python(request.param[0], picklefile)

def pytest_funcarg__python2(request):
    python1 = request.getfuncargvalue("python1")
    return Python(request.param[1], python1.picklefile)

def pytest_funcarg__obj(request):
    return request.param[2]

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
