""" monkeypatching and mocking functionality.  """

import os, sys

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

    All modifications will be undone after the requesting
    test function has finished. The ``raising``
    parameter determines if a KeyError or AttributeError
    will be raised if the set/deletion operation has no target.
    """
    mpatch = monkeypatch()
    request.addfinalizer(mpatch.undo)
    return mpatch

notset = object()

class monkeypatch:
    """ object keeping a record of setattr/item/env/syspath changes. """
    def __init__(self):
        self._setattr = []
        self._setitem = []

    def setattr(self, obj, name, value, raising=True):
        """ set attribute ``name`` on ``obj`` to ``value``, by default
        raise AttributeEror if the attribute did not exist. """
        oldval = getattr(obj, name, notset)
        if raising and oldval is notset:
            raise AttributeError("%r has no attribute %r" %(obj, name))
        self._setattr.insert(0, (obj, name, oldval))
        setattr(obj, name, value)

    def delattr(self, obj, name, raising=True):
        """ delete attribute ``name`` from ``obj``, by default raise
        AttributeError it the attribute did not previously exist. """
        if not hasattr(obj, name):
            if raising:
                raise AttributeError(name)
        else:
            self._setattr.insert(0, (obj, name, getattr(obj, name, notset)))
            delattr(obj, name)

    def setitem(self, dic, name, value):
        """ set dictionary entry ``name`` to value. """
        self._setitem.insert(0, (dic, name, dic.get(name, notset)))
        dic[name] = value

    def delitem(self, dic, name, raising=True):
        """ delete ``name`` from dict, raise KeyError if it doesn't exist."""
        if name not in dic:
            if raising:
                raise KeyError(name)
        else:
            self._setitem.insert(0, (dic, name, dic.get(name, notset)))
            del dic[name]

    def setenv(self, name, value, prepend=None):
        """ set environment variable ``name`` to ``value``.  if ``prepend``
        is a character, read the current environment variable value
        and prepend the ``value`` adjoined with the ``prepend`` character."""
        value = str(value)
        if prepend and name in os.environ:
            value = value + prepend + os.environ[name]
        self.setitem(os.environ, name, value)

    def delenv(self, name, raising=True):
        """ delete ``name`` from environment, raise KeyError it not exists."""
        self.delitem(os.environ, name, raising=raising)

    def syspath_prepend(self, path):
        """ prepend ``path`` to ``sys.path`` list of import locations. """
        if not hasattr(self, '_savesyspath'):
            self._savesyspath = sys.path[:]
        sys.path.insert(0, str(path))

    def undo(self):
        """ undo previous changes.  This call consumes the
        undo stack.  Calling it a second time has no effect unless
        you  do more monkeypatching after the undo call."""
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
