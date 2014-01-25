""" monkeypatching and mocking functionality.  """

import os, sys
from py.builtin import _basestring

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



def derive_importpath(import_path):
    import pytest
    if not isinstance(import_path, _basestring) or "." not in import_path:
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
            return attr, obj



notset = object()

class monkeypatch:
    """ object keeping a record of setattr/item/env/syspath changes. """
    def __init__(self):
        self._setattr = []
        self._setitem = []
        self._cwd = None

    def setattr(self, target, name, value=notset, raising=True):
        """ set attribute value on target, memorizing the old value.
        By default raise AttributeError if the attribute did not exist.

        For convenience you can specify a string as ``target`` which
        will be interpreted as a dotted import path, with the last part
        being the attribute name.  Example:
        ``monkeypatch.setattr("os.getcwd", lambda x: "/")``
        would set the ``getcwd`` function of the ``os`` module.

        The ``raising`` value determines if the setattr should fail
        if the attribute is not already present (defaults to True
        which means it will raise).
        """
        __tracebackhide__ = True
        import inspect

        if value is notset:
            if not isinstance(target, _basestring):
                raise TypeError("use setattr(target, name, value) or "
                   "setattr(target, value) with target being a dotted "
                   "import string")
            value = name
            name, target = derive_importpath(target)

        oldval = getattr(target, name, notset)
        if raising and oldval is notset:
            raise AttributeError("%r has no attribute %r" %(target, name))

        # avoid class descriptors like staticmethod/classmethod
        if inspect.isclass(target):
            oldval = target.__dict__.get(name, notset)
        self._setattr.insert(0, (target, name, oldval))
        setattr(target, name, value)

    def delattr(self, target, name=notset, raising=True):
        """ delete attribute ``name`` from ``target``, by default raise
        AttributeError it the attribute did not previously exist.

        If no ``name`` is specified and ``target`` is a string
        it will be interpreted as a dotted import path with the
        last part being the attribute name.

        If raising is set to false, the attribute is allowed to not
        pre-exist.
        """
        __tracebackhide__ = True
        if name is notset:
            if not isinstance(target, _basestring):
                raise TypeError("use delattr(target, name) or "
                                "delattr(target) with target being a dotted "
                                "import string")
            name, target = derive_importpath(target)

        if not hasattr(target, name):
            if raising:
                raise AttributeError(name)
        else:
            self._setattr.insert(0, (target, name,
                                     getattr(target, name, notset)))
            delattr(target, name)

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
