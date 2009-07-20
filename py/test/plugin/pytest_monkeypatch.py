"""
safely patch object attributes, dicts and environment variables. 

Usage
----------------

Use the `monkeypatch funcarg`_ to safely patch the environment
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

.. _`monkeypatch blog post`: http://tetamap.wordpress.com/2009/03/03/monkeypatching-in-unit-tests-done-right/
"""

import os

def pytest_funcarg__monkeypatch(request):
    """The returned ``monkeypatch`` funcarg provides three 
    helper methods to modify objects, dictionaries or os.environ::

        monkeypatch.setattr(obj, name, value)  
        monkeypatch.setitem(mapping, name, value) 
        monkeypatch.setenv(name, value) 

    All such modifications will be undone when the requesting 
    test function finished its execution. 
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

    def setitem(self, dictionary, name, value):
        self._setitem.insert(0, (dictionary, name, dictionary.get(name, notset)))
        dictionary[name] = value

    def setenv(self, name, value):
        self.setitem(os.environ, name, str(value))        

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

def test_setenv():
    monkeypatch = MonkeyPatch()
    monkeypatch.setenv('XYZ123', 2)
    import os
    assert os.environ['XYZ123'] == "2"
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
        
