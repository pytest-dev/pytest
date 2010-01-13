import os, sys
import py
from py._plugin.pytest_monkeypatch import MonkeyPatch

def test_setattr():
    class A:
        x = 1
    monkeypatch = MonkeyPatch()
    py.test.raises(AttributeError, "monkeypatch.setattr(A, 'notexists', 2)")
    monkeypatch.setattr(A, 'y', 2, raising=False)
    assert A.y == 2
    monkeypatch.undo()
    assert not hasattr(A, 'y')

    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(A, 'x', 2)
    assert A.x == 2
    monkeypatch.setattr(A, 'x', 3)
    assert A.x == 3
    monkeypatch.undo()
    assert A.x == 1

    A.x = 5
    monkeypatch.undo() # double-undo makes no modification
    assert A.x == 5

def test_delattr():
    class A:
        x = 1
    monkeypatch = MonkeyPatch()
    monkeypatch.delattr(A, 'x')
    assert not hasattr(A, 'x')
    monkeypatch.undo()
    assert A.x == 1

    monkeypatch = MonkeyPatch()
    monkeypatch.delattr(A, 'x')
    py.test.raises(AttributeError, "monkeypatch.delattr(A, 'y')")
    monkeypatch.delattr(A, 'y', raising=False)
    monkeypatch.setattr(A, 'x', 5, raising=False)
    assert A.x == 5
    monkeypatch.undo()
    assert A.x == 1

def test_setitem():
    d = {'x': 1}
    monkeypatch = MonkeyPatch()
    monkeypatch.setitem(d, 'x', 2)
    monkeypatch.setitem(d, 'y', 1700)
    monkeypatch.setitem(d, 'y', 1700)
    assert d['x'] == 2
    assert d['y'] == 1700
    monkeypatch.setitem(d, 'x', 3)
    assert d['x'] == 3
    monkeypatch.undo()
    assert d['x'] == 1
    assert 'y' not in d
    d['x'] = 5
    monkeypatch.undo()
    assert d['x'] == 5

def test_delitem():
    d = {'x': 1}
    monkeypatch = MonkeyPatch()
    monkeypatch.delitem(d, 'x')
    assert 'x' not in d
    monkeypatch.delitem(d, 'y', raising=False)
    py.test.raises(KeyError, "monkeypatch.delitem(d, 'y')")
    assert not d
    monkeypatch.setitem(d, 'y', 1700)
    assert d['y'] == 1700
    d['hello'] = 'world'
    monkeypatch.setitem(d, 'x', 1500)
    assert d['x'] == 1500
    monkeypatch.undo()
    assert d == {'hello': 'world', 'x': 1}

def test_setenv():
    monkeypatch = MonkeyPatch()
    monkeypatch.setenv('XYZ123', 2)
    import os
    assert os.environ['XYZ123'] == "2"
    monkeypatch.undo()
    assert 'XYZ123' not in os.environ

def test_delenv():
    name = 'xyz1234'
    assert name not in os.environ 
    monkeypatch = MonkeyPatch()
    py.test.raises(KeyError, "monkeypatch.delenv(%r, raising=True)" % name)
    monkeypatch.delenv(name, raising=False)
    monkeypatch.undo()
    os.environ[name] = "1"
    try:
        monkeypatch = MonkeyPatch()
        monkeypatch.delenv(name)
        assert name not in os.environ 
        monkeypatch.setenv(name, "3")
        assert os.environ[name] == "3"
        monkeypatch.undo()
        assert os.environ[name] == "1"
    finally:
        if name in os.environ:
            del os.environ[name]

def test_setenv_prepend():
    import os
    monkeypatch = MonkeyPatch()
    monkeypatch.setenv('XYZ123', 2, prepend="-")
    assert os.environ['XYZ123'] == "2"
    monkeypatch.setenv('XYZ123', 3, prepend="-")
    assert os.environ['XYZ123'] == "3-2"
    monkeypatch.undo()
    assert 'XYZ123' not in os.environ

def test_monkeypatch_plugin(testdir):
    reprec = testdir.inline_runsource("""
        pytest_plugins = 'pytest_monkeypatch', 
        def test_method(monkeypatch):
            assert monkeypatch.__class__.__name__ == "MonkeyPatch"
    """)
    res = reprec.countoutcomes()
    assert tuple(res) == (1, 0, 0), res

def test_syspath_prepend():
    old = list(sys.path)
    try:
        monkeypatch = MonkeyPatch()
        monkeypatch.syspath_prepend('world')
        monkeypatch.syspath_prepend('hello')
        assert sys.path[0] == "hello"
        assert sys.path[1] == "world"
        monkeypatch.undo()
        assert sys.path == old 
        monkeypatch.undo()
        assert sys.path == old 
    finally:
        sys.path[:] = old

            
