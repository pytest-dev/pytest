from __future__ import generators 

import py
import types
import sys

def checksubpackage(name):
    obj = getattr(py, name)
    if hasattr(obj, '__map__'): # isinstance(obj, Module):
        keys = dir(obj)
        assert len(keys) > 0
        assert getattr(obj, '__map__')  == {}

def test_dir():
    from py.__.initpkg import ApiModule
    for name in dir(py):
        if name == 'magic': # greenlets don't work everywhere, we don't care here
            continue
        if not name.startswith('_'):
            yield checksubpackage, name

from py.initpkg import ApiModule 
glob = []
class MyModule(ApiModule):
    def __init__(self, *args):
        glob.append(self.__dict__) 
        assert isinstance(glob[-1], (dict, type(None)))
        ApiModule.__init__(self, *args)

def test_early__dict__access():
    mymod = MyModule("whatever", "myname")
    assert isinstance(mymod.__dict__, dict) 
    
def test_resolve_attrerror(): 
    extpyish = "./initpkg.py", "hello"
    excinfo = py.test.raises(AttributeError, "py.__pkg__._resolve(extpyish)")
    s = str(excinfo.value)
    assert s.find(extpyish[0]) != -1
    assert s.find(extpyish[1]) != -1

def test_virtual_module_identity():
    from py import path as path1
    from py import path as path2
    assert path1 is path2
    from py.path import local as local1
    from py.path import local as local2
    assert local1 is local2

def test_importall():
    base = py.path.local(py.__file__).dirpath()
    nodirs = (
        base.join('test', 'testing', 'data'),
        base.join('apigen', 'tracer', 'testing', 'package'),
        base.join('test', 'testing', 'test'),
        base.join('test', 'rsession', 'webjs.py'),
        base.join('apigen', 'source', 'server.py'),
        base.join('magic', 'greenlet.py'), 
        base.join('path', 'gateway',),
        base.join('doc',),
        base.join('rest', 'directive.py'),
        base.join('test', 'testing', 'import_test'),
        base.join('c-extension',), 
        base.join('test', 'report', 'web.py'),
        base.join('test', 'report', 'webjs.py'),
        base.join('test', 'report', 'rest.py'),
        base.join('magic', 'greenlet.py'), 
        base.join('bin'),
        base.join('execnet', 'script'),
        base.join('compat', 'testing'),
    )
    def recurse(p):
        return p.check(dotfile=0) and p.basename != "attic"

    for p in base.visit('*.py', recurse):
        if p.basename == '__init__.py':
            continue
        relpath = p.new(ext='').relto(base)
        if base.sep in relpath: # not py/*.py itself
            for x in nodirs:
                if p == x or p.relto(x):
                    break
            else:
                relpath = relpath.replace(base.sep, '.')
                modpath = 'py.__.%s' % relpath
                yield check_import, modpath 

def check_import(modpath): 
    print "checking import", modpath
    assert __import__(modpath) 

def test_shahexdigest():
    hex = py.__pkg__.shahexdigest()
    assert len(hex) == 40

def test_getzipdata():
    s = py.__pkg__.getzipdata()

def test_getrev():
    if not py.path.local(py.__file__).dirpath('.svn').check():
        py.test.skip("py package is not a svn checkout") 
    d = py.__pkg__.getrev()
    svnversion = py.path.local.sysfind('svnversion')
    if svnversion is None:
        py.test.skip("cannot test svnversion, 'svnversion' binary not found")
    v = svnversion.sysexec(py.path.local(py.__file__).dirpath())
    assert v.startswith(str(d))

# the following test should abasically work in the future
def XXXtest_virtual_on_the_fly():
    py.initpkg('my', {
        'x.abspath' : 'os.path.abspath',
        'x.local'   : 'py.path.local',
        'y'   : 'smtplib',
        'z.cmdexec'   : 'py.process.cmdexec',
    })
    from my.x import abspath
    from my.x import local
    import smtplib
    from my import y
    assert y is smtplib
    from my.z import cmdexec
    from py.process import cmdexec as cmdexec2
    assert cmdexec is cmdexec2

#
# test support for importing modules
#

class TestRealModule:

    def setup_class(cls):
        cls.tmpdir = py.test.ensuretemp('test_initpkg')
        sys.path = [str(cls.tmpdir)] + sys.path
        pkgdir = cls.tmpdir.ensure('realtest', dir=1)

        tfile = pkgdir.join('__init__.py')
        tfile.write(py.code.Source("""
            import py
            py.initpkg('realtest', {
                'x.module.__doc__': ('./testmodule.py', '__doc__'),
                'x.module': ('./testmodule.py', '*'), 
            })
        """))

        tfile = pkgdir.join('testmodule.py')
        tfile.write(py.code.Source("""
            'test module'

            __all__ = ['mytest0', 'mytest1', 'MyTest']
        
            def mytest0():
                pass
            def mytest1():
                pass
            class MyTest:
                pass

        """))

        import realtest # need to mimic what a user would do
        #py.initpkg('realtest', {
        #    'module': ('./testmodule.py', None)
        #})

    def setup_method(self, *args):
        """Unload the test modules before each test."""
        module_names = ['realtest', 'realtest.x', 'realtest.x.module']
        for modname in module_names:
            if modname in sys.modules:
                del sys.modules[modname]

    def test_realmodule(self):
        """Testing 'import realtest.x.module'"""
        import realtest.x.module
        assert 'realtest.x.module' in sys.modules
        assert getattr(realtest.x.module, 'mytest0')

    def test_realmodule_from(self):
        """Testing 'from test import module'."""
        from realtest.x import module
        assert getattr(module, 'mytest1')

    def test_realmodule_star(self):
        """Testing 'from test.module import *'."""
        tfile = self.tmpdir.join('startest.py')
        tfile.write(py.code.Source("""
            from realtest.x.module import *
            globals()['mytest0']
            globals()['mytest1']
            globals()['MyTest']
        """))
        import startest # an exception will be raise if an error occurs

    def test_realmodule_dict_import(self):
        "Test verifying that accessing the __dict__ invokes the import"
        import realtest.x.module
        moddict = realtest.x.module.__dict__ 
        assert 'mytest0' in moddict
        assert 'mytest1' in moddict
        assert 'MyTest' in moddict

    def test_realmodule___doc__(self):
        """test whether the __doc__ attribute is set properly from initpkg"""
        import realtest.x.module
        assert realtest.x.module.__doc__ == 'test module'

#class TestStdHook:
#    """Tests imports for the standard Python library hook."""
#
#    def setup_method(self, *args):
#        """Unload the test modules before each test."""
#        module_names = ['py.std.StringIO', 'py.std', 'py']
#        for modname in module_names:
#            if modname in sys.modules:
#                del sys.modules[modname]
#
#    def test_std_import_simple(self):
#        import py
#        StringIO = py.std.StringIO
#        assert 'py' in sys.modules
#        assert 'py.std' in sys.modules
#        assert 'py.std.StringIO' in sys.modules
#        assert hasattr(py.std.StringIO, 'StringIO')
#
#    def test_std_import0(self):
#        """Testing 'import py.std.StringIO'."""
#        import py.std.StringIO
#        assert 'py' in sys.modules
#        assert 'py.std' in sys.modules
#        assert 'py.std.StringIO' in sys.modules
#        assert hasattr(py.std.StringIO, 'StringIO')
#
#    def test_std_import1(self):
#        """Testing 'from py import std'."""
#        from py import std
#        assert 'py' in sys.modules
#        assert 'py.std' in sys.modules
#
#    def test_std_from(self):
#        """Testing 'from py.std import StringIO'."""
#        from py.std import StringIO
#        assert getattr(StringIO, 'StringIO')
#
#    def test_std_star(self):
#        "Test from py.std.string import *"
#        """Testing 'from test.module import *'."""
#        tmpdir = py.test.ensuretemp('test_initpkg')
#        tfile = tmpdir.join('stdstartest.py')
#        tfile.write(py.code.Source("""if True:
#            from realtest.module import *
#            globals()['mytest0']
#            globals()['mytest1']
#            globals()['MyTest']
#        """))
#        import stdstartest  # an exception will be raise if an error occurs

##def test_help():
#    help(std.path)
#    #assert False


def test_autoimport():
    from py.initpkg import autoimport
    py.std.os.environ['AUTOTEST_AUTOIMPORT'] = "nonexistmodule"
    py.test.raises(ImportError, "autoimport('autotest')")
