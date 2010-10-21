import py

from pytest.plugin.tmpdir import pytest_funcarg__tmpdir
from pytest.plugin.python import FuncargRequest

def test_funcarg(testdir):
    item = testdir.getitem("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall(id='a')
                metafunc.addcall(id='b')
            def test_func(tmpdir): pass
            """, 'test_func[a]')
    p = pytest_funcarg__tmpdir(FuncargRequest(item))
    assert p.check()
    bn = p.basename.strip("0123456789")
    assert bn.endswith("test_func_a_")
    item.name = "qwe/\\abc"
    p = pytest_funcarg__tmpdir(FuncargRequest(item))
    assert p.check()
    bn = p.basename.strip("0123456789")
    assert bn == "qwe__abc"

def test_ensuretemp(recwarn):
    #py.test.deprecated_call(py.test.ensuretemp, 'hello')
    d1 = py.test.ensuretemp('hello')
    d2 = py.test.ensuretemp('hello')
    assert d1 == d2
    assert d1.check(dir=1)

