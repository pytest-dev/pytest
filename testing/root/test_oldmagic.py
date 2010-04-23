import py
import sys, os

def fass():
    assert 1 == 2
def check_assertion():
    excinfo = py.test.raises(AssertionError, fass)
    s = excinfo.exconly(tryshort=True)
    if not s == "assert 1 == 2":
        raise ValueError("assertion not enabled: got %s" % s)

def test_invoke_assertion(recwarn, monkeypatch):
    monkeypatch.setattr(py.builtin.builtins, 'AssertionError', None)
    py.magic.invoke(assertion=True)
    try:
        check_assertion()
    finally:
        py.magic.revoke(assertion=True)
    recwarn.pop(DeprecationWarning)

@py.test.mark.skipif("sys.platform.startswith('java')")
def test_invoke_compile(recwarn, monkeypatch):
    monkeypatch.setattr(py.builtin.builtins, 'compile', None)
    py.magic.invoke(compile=True)
    try:
        co = compile("""if 1: 
                    def f(): 
                        return 1
                    \n""", '', 'exec')
        d = {}
        py.builtin.exec_(co, d)
        assert py.code.Source(d['f']) 
    finally:
        py.magic.revoke(compile=True)
    recwarn.pop(DeprecationWarning)

def test_patch_revert(recwarn):
    class a:
        pass
    py.test.raises(AttributeError, "py.magic.patch(a, 'i', 42)")

    a.i = 42
    py.magic.patch(a, 'i', 23)
    assert a.i == 23
    recwarn.pop(DeprecationWarning)
    py.magic.revert(a, 'i')
    assert a.i == 42
    recwarn.pop(DeprecationWarning)

def test_double_patch(recwarn):
    class a:
        i = 42
    assert py.magic.patch(a, 'i', 2) == 42
    recwarn.pop(DeprecationWarning)
    assert py.magic.patch(a, 'i', 3) == 2
    assert a.i == 3
    assert py.magic.revert(a, 'i') == 3
    recwarn.pop(DeprecationWarning)
    assert a.i == 2
    assert py.magic.revert(a, 'i') == 2
    assert a.i == 42

def test_valueerror(recwarn):
    class a:
        i = 2
        pass
    py.test.raises(ValueError, "py.magic.revert(a, 'i')")
    recwarn.pop(DeprecationWarning)

def test_AssertionError(testdir):
    testdir.makepyfile("""
        import py
        def test_hello(recwarn):
            err = py.magic.AssertionError
            recwarn.pop(DeprecationWarning)
            assert err is py.code._AssertionError
    """)
    result = testdir.runpytest() 
    assert "1 passed" in result.stdout.str()

def test_autopath_deprecation(testdir):
    testdir.makepyfile("""
        import py
        def test_hello(recwarn):
            p = py.magic.autopath()
            recwarn.pop(DeprecationWarning)
            assert py.path.local(__file__).dirpath() == p.dirpath()
    """)
    result = testdir.runpytest() 
    assert "1 passed" in result.stdout.str()

class Testautopath:
    getauto = "from py.magic import autopath ; autopath = autopath()"
    def setup_class(cls): 
        cls.root = py.test.ensuretemp(cls.__name__) 
        cls.initdir = cls.root.ensure('pkgdir', dir=1)
        cls.initdir.ensure('__init__.py')
        cls.initdir2 = cls.initdir.ensure('initdir2', dir=1)
        cls.initdir2.ensure('__init__.py')

    def test_import_autoconfigure__file__with_init(self):
        testpath = self.initdir2 / 'autoconfiguretest.py'
        d = {'__file__' : str(testpath)}
        oldsyspath = sys.path[:]
        try:
            py.builtin.exec_(self.getauto, d)
            conf = d['autopath']
            assert conf.dirpath() == self.initdir2
            assert conf.pkgdir == self.initdir
            assert str(self.root) in sys.path
            py.builtin.exec_(self.getauto, d)
            assert conf is not d['autopath']
        finally:
            sys.path[:] = oldsyspath

    def test_import_autoconfigure__file__with_py_exts(self):
        for ext in '.pyc', '.pyo':
            testpath = self.initdir2 / ('autoconfiguretest' + ext)
            d = {'__file__' : str(testpath)}
            oldsyspath = sys.path[:]
            try:
                py.builtin.exec_(self.getauto, d)
                conf = d['autopath']
                assert conf == self.initdir2.join('autoconfiguretest.py')
                assert conf.pkgdir == self.initdir
                assert str(self.root) in sys.path
                py.builtin.exec_(self.getauto, d)
                assert conf is not d['autopath']
            finally:
                sys.path[:] = oldsyspath

    def test_import_autoconfigure___file__without_init(self):
        testpath = self.root / 'autoconfiguretest.py'
        d = {'__file__' : str(testpath)}
        oldsyspath = sys.path[:]
        try:
            py.builtin.exec_(self.getauto, d)
            conf = d['autopath']
            assert conf.dirpath() == self.root
            assert conf.pkgdir == self.root
            syspath = sys.path[:]
            assert str(self.root) in syspath
            py.builtin.exec_(self.getauto, d)
            assert conf is not d['autopath']
        finally:
            sys.path[:] = oldsyspath

    def test_import_autoconfigure__nofile(self):
        p = self.initdir2 / 'autoconfiguretest.py'
        oldsysarg = sys.argv
        sys.argv = [str(p)]
        oldsyspath = sys.path[:]
        try:
            d = {}
            py.builtin.exec_(self.getauto, d)
            conf = d['autopath']
            assert conf.dirpath() == self.initdir2
            assert conf.pkgdir == self.initdir
            syspath = sys.path[:]
            assert str(self.root) in syspath
        finally:
            sys.path[:] = oldsyspath
            sys.argv = sys.argv


    def test_import_autoconfigure__nofile_interactive(self):
        oldsysarg = sys.argv
        sys.argv = ['']
        oldsyspath = sys.path[:]
        try:
            py.test.raises(ValueError,'''
                d = {}
                py.builtin.exec_(self.getauto, d)
            ''')
        finally:
            sys.path[:] = oldsyspath
            sys.argv = sys.argv
