import py
import sys

class TestAutoPath:
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
            exec self.getauto in d
            conf = d['autopath']
            assert conf.dirpath() == self.initdir2
            assert conf.pkgdir == self.initdir
            assert str(self.root) in sys.path
            exec self.getauto in d
            assert conf is not d['autopath']
        finally:
            sys.path[:] = oldsyspath

    def test_import_autoconfigure__file__with_py_exts(self):
        for ext in '.pyc', '.pyo':
            testpath = self.initdir2 / ('autoconfiguretest' + ext)
            d = {'__file__' : str(testpath)}
            oldsyspath = sys.path[:]
            try:
                exec self.getauto in d
                conf = d['autopath']
                assert conf == self.initdir2.join('autoconfiguretest.py')
                assert conf.pkgdir == self.initdir
                assert str(self.root) in sys.path
                exec self.getauto in d
                assert conf is not d['autopath']
            finally:
                sys.path[:] = oldsyspath

    def test_import_autoconfigure___file__without_init(self):
        testpath = self.root / 'autoconfiguretest.py'
        d = {'__file__' : str(testpath)}
        oldsyspath = sys.path[:]
        try:
            exec self.getauto in d
            conf = d['autopath']
            assert conf.dirpath() == self.root
            assert conf.pkgdir == self.root
            syspath = sys.path[:]
            assert str(self.root) in syspath
            exec self.getauto in d
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
            exec self.getauto in d
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
                exec self.getauto in d
            ''')
        finally:
            sys.path[:] = oldsyspath
            sys.argv = sys.argv
