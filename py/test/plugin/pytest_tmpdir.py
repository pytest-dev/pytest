"""
example:

    pytest_plugins = "pytest_tmpdir" 

    def test_plugin(tmpdir):
        tmpdir.join("hello").write("hello")

"""
import py

class TmpdirPlugin:
    """ provide temporary directories to test functions and methods. 
    """ 

    def pytest_pyfuncarg_tmpdir(self, pyfuncitem):
        name = pyfuncitem.name
        return pyfuncitem._config.mktemp(name, numbered=True)

# ===============================================================================
#
# plugin tests 
#
# ===============================================================================
#
def test_generic(plugintester):
    plugintester.apicheck(TmpdirPlugin)

def test_pyfuncarg(testdir):
    item = testdir.getitem("def test_func(tmpdir): pass")
    plugin = TmpdirPlugin()
    p = plugin.pytest_pyfuncarg_tmpdir(item)
    assert p.check()
    bn = p.basename.strip("0123456789-")
    assert bn.endswith("test_func")
