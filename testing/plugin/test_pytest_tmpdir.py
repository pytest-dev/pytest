from py._plugin.pytest_tmpdir import pytest_funcarg__tmpdir

def test_funcarg(testdir):
    from py._test.funcargs import FuncargRequest
    item = testdir.getitem("def test_func(tmpdir): pass")
    p = pytest_funcarg__tmpdir(FuncargRequest(item))
    assert p.check()
    bn = p.basename.strip("0123456789")
    assert bn.endswith("test_func")
