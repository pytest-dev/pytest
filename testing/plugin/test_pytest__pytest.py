import py
from py.plugin.pytest__pytest import HookRecorder

def test_hookrecorder_basic():
    comregistry = py._com.Registry() 
    rec = HookRecorder(comregistry)
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
    import sys
    comregistry = py._com.Registry() 
    rec = HookRecorder(comregistry)
    apimod = type(sys)('api')
    def xyz():
        pass
    apimod.xyz = xyz
    rec.start_recording(apimod)
    rec.hook.xyz()
    call = rec.popcall("xyz")
    assert call._name == "xyz"

reg = py._com.comregistry
def test_functional_default(testdir, _pytest):
    assert _pytest.comregistry == py._com.comregistry 
    assert _pytest.comregistry != reg

def test_functional(testdir, linecomp):
    reprec = testdir.inline_runsource("""
        import py
        pytest_plugins="_pytest"
        def test_func(_pytest):
            class ApiClass:
                def xyz(self, arg):  pass 
            rec = _pytest.gethookrecorder(ApiClass)
            class Plugin:
                def xyz(self, arg):
                    return arg + 1
            rec._comregistry.register(Plugin())
            res = rec.hook.xyz(arg=41)
            assert res == [42]
    """)
    reprec.assertoutcome(passed=1)
