import py

@py.test.mark.xfail
def test_hello():
    assert 0

@py.test.mark.xfail(run=False)
def test_hello2():
    assert 0

@py.test.mark.xfail("hasattr(os, 'sep')")
def test_hello3():
    assert 0

def test_hello5():
    py.test.xfail("reason")
