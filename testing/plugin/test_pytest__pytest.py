import py
import os, sys
from py._plugin.pytest__pytest import HookRecorder
from py._test.pluginmanager import Registry

def test_hookrecorder_basic():
    rec = HookRecorder(Registry())
    class ApiClass:
        def pytest_xyz(self, arg):
            "x"
    rec.start_recording(ApiClass)
    rec.hook.pytest_xyz(arg=123)
    call = rec.popcall("pytest_xyz")
    assert call.arg == 123 
    assert call._name == "pytest_xyz"
    py.test.raises(ValueError, "rec.popcall('abc')")

def test_hookrecorder_basic_no_args_hook():
    rec = HookRecorder(Registry())
    apimod = type(os)('api')
    def pytest_xyz():
        "x"
    apimod.pytest_xyz = pytest_xyz
    rec.start_recording(apimod)
    rec.hook.pytest_xyz()
    call = rec.popcall("pytest_xyz")
    assert call._name == "pytest_xyz"

def test_functional(testdir, linecomp):
    reprec = testdir.inline_runsource("""
        import py
        from py._test.pluginmanager import HookRelay, Registry
        pytest_plugins="_pytest"
        def test_func(_pytest):
            class ApiClass:
                def pytest_xyz(self, arg):  "x"
            hook = HookRelay([ApiClass], Registry())
            rec = _pytest.gethookrecorder(hook)
            class Plugin:
                def pytest_xyz(self, arg):
                    return arg + 1
            rec._registry.register(Plugin())
            res = rec.hook.pytest_xyz(arg=41)
            assert res == [42]
    """)
    reprec.assertoutcome(passed=1)
