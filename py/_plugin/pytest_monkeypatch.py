"""
safely patch object attributes, dicts and environment variables. 

Usage 
----------------

Use the `monkeypatch funcarg`_ to tweak your global test environment 
for running a particular test.  You can safely set/del an attribute, 
dictionary item or environment variable by respective methods
on the monkeypatch funcarg.  If you want e.g. to set an ENV1 variable 
and have os.path.expanduser return a particular directory, you can 
write it down like this:

.. sourcecode:: python 

    def test_mytest(monkeypatch):
        monkeypatch.setenv('ENV1', 'myval')
        monkeypatch.setattr(os.path, 'expanduser', lambda x: '/tmp/xyz')
        ... # your test code that uses those patched values implicitely

After the test function finished all modifications will be undone, 
because the ``monkeypatch.undo()`` method is registered as a finalizer. 

``monkeypatch.setattr/delattr/delitem/delenv()`` all 
by default raise an Exception if the target does not exist. 
Pass ``raising=False`` if you want to skip this check. 

prepending to PATH or other environment variables 
---------------------------------------------------------

To prepend a value to an already existing environment parameter:

.. sourcecode:: python 

    def test_mypath_finding(monkeypatch):
        monkeypatch.setenv('PATH', 'x/y', prepend=":")
        # in bash language: export PATH=x/y:$PATH 

calling "undo" finalization explicitely
-----------------------------------------

At the end of function execution py.test invokes
a teardown hook which undoes all monkeypatch changes. 
If you do not want to wait that long you can call 
finalization explicitely::

    monkeypatch.undo()  

This will undo previous changes.  This call consumes the
undo stack.  Calling it a second time has no effect unless
you  start monkeypatching after the undo call. 

.. _`monkeypatch blog post`: http://tetamap.wordpress.com/2009/03/03/monkeypatching-in-unit-tests-done-right/
"""

import py, os, sys

def pytest_funcarg__monkeypatch(request):
    """The returned ``monkeypatch`` funcarg provides these 
    helper methods to modify objects, dictionaries or os.environ::

        monkeypatch.setattr(obj, name, value, raising=True)  
        monkeypatch.delattr(obj, name, raising=True)
        monkeypatch.setitem(mapping, name, value) 
        monkeypatch.delitem(obj, name, raising=True)
        monkeypatch.setenv(name, value, prepend=False) 
        monkeypatch.delenv(name, value, raising=True)
        monkeypatch.syspath_prepend(path)

    All modifications will be undone when the requesting 
    test function finished its execution.  The ``raising`` 
    parameter determines if a KeyError or AttributeError 
    will be raised if the set/deletion operation has no target. 
    """
    monkeypatch = MonkeyPatch()
    request.addfinalizer(monkeypatch.undo)
    return monkeypatch

notset = object()

class MonkeyPatch:
    def __init__(self):
        self._setattr = []
        self._setitem = []

    def setattr(self, obj, name, value, raising=True):
        oldval = getattr(obj, name, notset)
        if raising and oldval is notset:
            raise AttributeError("%r has no attribute %r" %(obj, name))
        self._setattr.insert(0, (obj, name, oldval))
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

    def syspath_prepend(self, path):
        if not hasattr(self, '_savesyspath'):
            self._savesyspath = sys.path[:]
        sys.path.insert(0, str(path))

    def undo(self):
        for obj, name, value in self._setattr:
            if value is not notset:
                setattr(obj, name, value)
            else:
                delattr(obj, name)
        self._setattr[:] = []
        for dictionary, name, value in self._setitem:
            if value is notset:
                del dictionary[name]
            else:
                dictionary[name] = value
        self._setitem[:] = []
        if hasattr(self, '_savesyspath'):
            sys.path[:] = self._savesyspath
