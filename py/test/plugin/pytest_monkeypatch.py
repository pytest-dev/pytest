"""
safely patch object attributes, dicts and environment variables. 

Usage
----------------

Use the `monkeypatch funcarg`_ to safely patch environment
variables, object attributes or dictionaries.  For example, if you want
to set the environment variable ``ENV1`` and patch the
``os.path.abspath`` function to return a particular value during a test
function execution you can write it down like this:

.. sourcecode:: python 

    def test_mytest(monkeypatch):
        monkeypatch.setenv('ENV1', 'myval')
        monkeypatch.setattr(os.path, 'abspath', lambda x: '/')
        ... # your test code 

The function argument will do the modifications and memorize the 
old state.  After the test function finished execution all 
modifications will be reverted.  See the `monkeypatch blog post`_ 
for an extensive discussion.  

To add to a possibly existing environment parameter you
can use this example: 

.. sourcecode:: python 

    def test_mypath_finding(monkeypatch):
        monkeypatch.setenv('PATH', 'x/y', prepend=":")
        #  x/y will be at the beginning of $PATH 

.. _`monkeypatch blog post`: http://tetamap.wordpress.com/2009/03/03/monkeypatching-in-unit-tests-done-right/
"""

import py, os

def pytest_funcarg__monkeypatch(request):
    """The returned ``monkeypatch`` funcarg provides these 
    helper methods to modify objects, dictionaries or os.environ::

        monkeypatch.setattr(obj, name, value)  
        monkeypatch.delattr(obj, name, raising=True)
        monkeypatch.setitem(mapping, name, value) 
        monkeypatch.delitem(obj, name, raising=True)
        monkeypatch.setenv(name, value, prepend=False) 
        monkeypatch.delenv(name, value, raising=True)

    All modifications will be undone when the requesting 
    test function finished its execution.  For the ``del`` 
    methods the ``raising`` parameter determines if a
    KeyError or AttributeError will be raised if the
    deletion has no target. 
    """
    monkeypatch = MonkeyPatch()
    request.addfinalizer(monkeypatch.finalize)
    return monkeypatch

notset = object()

class MonkeyPatch:
    def __init__(self):
        self._setattr = []
        self._setitem = []

    def setattr(self, obj, name, value):
        self._setattr.insert(0, (obj, name, getattr(obj, name, notset)))
        setattr(obj, name, value)

    def delattr(self, obj, name, raising=True):
        if not hasattr(obj, name):
            if raising:
                raise AttributeError(name) 
        else:
            self._setattr.insert(0, (obj, name, getattr(obj, name, notset)))
            delattr(obj, name)

    def setitem(self, dic, name, value):
        self._setitem.insert(0, (dic, name, dic.get(name, notset)))
        dic[name] = value

    def delitem(self, dic, name, raising=True):
        if name not in dic:
            if raising:
                raise KeyError(name) 
        else:    
            self._setitem.insert(0, (dic, name, dic.get(name, notset)))
            del dic[name]

    def setenv(self, name, value, prepend=None):
        value = str(value)
        if prepend and name in os.environ:
            value = value + prepend + os.environ[name]
        self.setitem(os.environ, name, value)

    def delenv(self, name, raising=True):
        self.delitem(os.environ, name, raising=raising)

    def finalize(self):
        for obj, name, value in self._setattr:
            if value is not notset:
                setattr(obj, name, value)
            else:
                delattr(obj, name)
        for dictionary, name, value in self._setitem:
            if value is notset:
                del dictionary[name]
            else:
                dictionary[name] = value


def test_setattr():
    class A:
        x = 1
    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(A, 'x', 2)
    assert A.x == 2
    monkeypatch.setattr(A, 'x', 3)
    assert A.x == 3
    monkeypatch.finalize()
    assert A.x == 1

    monkeypatch.setattr(A, 'y', 3)
    assert A.y == 3
    monkeypatch.finalize()
    assert not hasattr(A, 'y')
     
def test_delattr():
    class A:
        x = 1
    monkeypatch = MonkeyPatch()
    monkeypatch.delattr(A, 'x')
    assert not hasattr(A, 'x')
    monkeypatch.finalize()
    assert A.x == 1

    monkeypatch = MonkeyPatch()
    monkeypatch.delattr(A, 'x')
    py.test.raises(AttributeError, "monkeypatch.delattr(A, 'y')")
    monkeypatch.delattr(A, 'y', raising=False)
    monkeypatch.setattr(A, 'x', 5)
    assert A.x == 5
    monkeypatch.finalize()
    assert A.x == 1

def test_setitem():
    d = {'x': 1}
    monkeypatch = MonkeyPatch()
    monkeypatch.setitem(d, 'x', 2)
    monkeypatch.setitem(d, 'y', 1700)
    assert d['x'] == 2
    assert d['y'] == 1700
    monkeypatch.setitem(d, 'x', 3)
    assert d['x'] == 3
    monkeypatch.finalize()
    assert d['x'] == 1
    assert 'y' not in d

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
    monkeypatch.finalize()
    assert d == {'hello': 'world', 'x': 1}

def test_setenv():
    monkeypatch = MonkeyPatch()
    monkeypatch.setenv('XYZ123', 2)
    import os
    assert os.environ['XYZ123'] == "2"
    monkeypatch.finalize()
    assert 'XYZ123' not in os.environ

def test_delenv():
    name = 'xyz1234'
    assert name not in os.environ 
    monkeypatch = MonkeyPatch()
    py.test.raises(KeyError, "monkeypatch.delenv(%r, raising=True)" % name)
    monkeypatch.delenv(name, raising=False)
    monkeypatch.finalize()
    os.environ[name] = "1"
    try:
        monkeypatch = MonkeyPatch()
        monkeypatch.delenv(name)
        assert name not in os.environ 
        monkeypatch.setenv(name, "3")
        assert os.environ[name] == "3"
        monkeypatch.finalize()
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
    monkeypatch.finalize()
    assert 'XYZ123' not in os.environ

def test_monkeypatch_plugin(testdir):
    reprec = testdir.inline_runsource("""
        pytest_plugins = 'pytest_monkeypatch', 
        def test_method(monkeypatch):
            assert monkeypatch.__class__.__name__ == "MonkeyPatch"
    """)
    res = reprec.countoutcomes()
    assert tuple(res) == (1, 0, 0), res
        
