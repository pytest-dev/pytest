
from py.test import raises
import py
import sys
import inspect

class TestAPI_V0_namespace_consistence:
    def test_path_entrypoints(self):
        assert inspect.ismodule(py.path)
        assert_class('py.path', 'local')
        assert_class('py.path', 'svnwc')
        assert_class('py.path', 'svnurl')

    def test_magic_entrypoints(self):
        assert_function('py.magic', 'invoke')
        assert_function('py.magic', 'revoke')
        assert_function('py.magic', 'patch')
        assert_function('py.magic', 'revoke')

    def test_process_entrypoints(self):
        assert_function('py.process', 'cmdexec')

    def XXXtest_utest_entrypoints(self):
        # XXX TOBECOMPLETED
        assert_function('py.test', 'main')
        #assert_module('std.utest', 'collect')

def assert_class(modpath, name):
    mod = __import__(modpath, None, None, [name])
    obj = getattr(mod, name)
    assert inspect.isclass(obj)

    # we don't test anymore that the exported classes have 
    # the exported module path and name on them. 
    #fullpath = modpath + '.' + name
    #assert obj.__module__ == modpath
    #if sys.version_info >= (2,3):
    #    assert obj.__name__ == name

def assert_function(modpath, name):
    mod = __import__(modpath, None, None, [name])
    obj = getattr(mod, name)
    assert hasattr(obj, 'func_doc')
    #assert obj.func_name == name
