""" monkeypatching and mocking functionality.  """

import os, sys, inspect
import pytest

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
        monkeypatch.chdir(path)

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
        self._cwd = None

    def replace(self, import_path, value):
        """ replace the object specified by a dotted ``import_path``
        with the given ``value``.

        For example ``replace("os.path.abspath", value)`` will
        trigger an ``import os.path`` and a subsequent
        setattr(os.path, "abspath", value).  Or to prevent
        the requests library from performing requests you can call
        ``replace("requests.sessions.Session.request", None)``
        which will lead to an import of ``requests.sessions`` and a call
        to ``setattr(requests.sessions.Session, "request", None)``.
        """
        if not isinstance(import_path, str) or "." not in import_path:
            raise TypeError("must be absolute import path string, not %r" %
                            (import_path,))
        rest = []
        target = import_path
        while target:
            try:
                obj = __import__(target, None, None, "__doc__")
            except ImportError:
                if "." not in target:
                    __tracebackhide__ = True
                    pytest.fail("could not import any sub part: %s" %
                                import_path)
                target, name = target.rsplit(".", 1)
                rest.append(name)
            else:
                assert rest
                try:
                    while len(rest) > 1:
                        attr = rest.pop()
                        obj = getattr(obj, attr)
                    attr = rest[0]
                    getattr(obj, attr)
                except AttributeError:
                    __tracebackhide__ = True
                    pytest.fail("object %r has no attribute %r" % (obj, attr))
                return self.setattr(obj, attr, value)

    def setattr(self, obj, name, value, raising=True):
        """ set attribute ``name`` on ``obj`` to ``value``, by default
        raise AttributeEror if the attribute did not exist.

        """
        oldval = getattr(obj, name, notset)
        if raising and oldval is notset:
            raise AttributeError("%r has no attribute %r" %(obj, name))

        # avoid class descriptors like staticmethod/classmethod
        if inspect.isclass(obj):
            oldval = obj.__dict__.get(name, notset)
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

    def chdir(self, path):
        """ change the current working directory to the specified path
        path can be a string or a py.path.local object
        """
        if self._cwd is None:
            self._cwd = os.getcwd()
        if hasattr(path, "chdir"):
            path.chdir()
        else:
            os.chdir(path)

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
                try:
                    del dictionary[name]
                except KeyError:
                    pass # was already deleted, so we have the desired state
            else:
                dictionary[name] = value
        self._setitem[:] = []
        if hasattr(self, '_savesyspath'):
            sys.path[:] = self._savesyspath
            del self._savesyspath

        if self._cwd is not None:
            os.chdir(self._cwd)
            self._cwd = None
