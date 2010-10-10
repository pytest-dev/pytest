import py

from pytest.plugin.pytest_tmpdir import pytest_funcarg__tmpdir
from pytest.plugin.pytest_python import FuncargRequest

def test_funcarg(testdir):
    item = testdir.getitem("def test_func(tmpdir): pass")
    p = pytest_funcarg__tmpdir(FuncargRequest(item))
    assert p.check()
    bn = p.basename.strip("0123456789")
    assert bn.endswith("test_func")

def test_ensuretemp(recwarn):
    #py.test.deprecated_call(py.test.ensuretemp, 'hello')
    d1 = py.test.ensuretemp('hello')
    d2 = py.test.ensuretemp('hello')
    assert d1 == d2
    assert d1.check(dir=1)

