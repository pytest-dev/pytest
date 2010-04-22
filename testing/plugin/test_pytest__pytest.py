import py
import sys
from py._plugin.pytest__pytest import HookRecorder
from py._test.pluginmanager import Registry

def test_hookrecorder_basic():
    rec = HookRecorder(Registry())
    class ApiClass:
        def xyz(self, arg):
            pass
    rec.start_recording(ApiClass)
    rec.hook.xyz(arg=123)
    call = rec.popcall("xyz")
    assert call.arg == 123 
    assert call._name == "xyz"
    py.test.raises(ValueError, "rec.popcall('abc')")

def test_hookrecorder_basic_no_args_hook():
    rec = HookRecorder(Registry())
    apimod = type(sys)('api')
    def xyz():
        pass
    apimod.xyz = xyz
    rec.start_recording(apimod)
    rec.hook.xyz()
    call = rec.popcall("xyz")
    assert call._name == "xyz"

def test_functional(testdir, linecomp):
    reprec = testdir.inline_runsource("""
        import py
        from py._test.pluginmanager import HookRelay, Registry
        pytest_plugins="_pytest"
        def test_func(_pytest):
            class ApiClass:
                def xyz(self, arg):  pass 
            hook = HookRelay([ApiClass], Registry())
            rec = _pytest.gethookrecorder(hook)
            class Plugin:
                def xyz(self, arg):
                    return arg + 1
            rec._registry.register(Plugin())
            res = rec.hook.xyz(arg=41)
            assert res == [42]
    """)
    reprec.assertoutcome(passed=1)
