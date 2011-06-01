""" generic mechanism for marking and selecting python functions. """
import pytest, py

def pytest_namespace():
    return {'mark': MarkGenerator()}

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('-k',
        action="store", dest="keyword", default='', metavar="KEYWORDEXPR",
        help="only run tests which match given keyword expression.  "
             "An expression consists of space-separated terms. "
             "Each term must match. Precede a term with '-' to negate. "
             "Terminate expression with ':' to make the first match match "
             "all subsequent tests (usually file-order). ")

def pytest_collection_modifyitems(items, config):
    keywordexpr = config.option.keyword
    if not keywordexpr:
        return
    selectuntil = False
    if keywordexpr[-1] == ":":
        selectuntil = True
        keywordexpr = keywordexpr[:-1]

    remaining = []
    deselected = []
    for colitem in items:
        if keywordexpr and skipbykeyword(colitem, keywordexpr):
            deselected.append(colitem)
        else:
            remaining.append(colitem)
            if selectuntil:
                keywordexpr = None

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining

def skipbykeyword(colitem, keywordexpr):
    """ return True if they given keyword expression means to
        skip this collector/item.
    """
    if not keywordexpr:
        return
    
    itemkeywords = getkeywords(colitem)
    for key in filter(None, keywordexpr.split()):
        eor = key[:1] == '-'
        if eor:
            key = key[1:]
        if not (eor ^ matchonekeyword(key, itemkeywords)):
            return True

def getkeywords(node):
    keywords = {}
    while node is not None:
        keywords.update(node.keywords)
        node = node.parent
    return keywords


def matchonekeyword(key, itemkeywords):
    for elem in key.split("."):
        for kw in itemkeywords:
            if elem in kw:
                break
        else:
            return False
    return True

class MarkGenerator:
    """ Factory for :class:`MarkDecorator` objects - exposed as
    a ``py.test.mark`` singleton instance.  Example::

         import py
         @py.test.mark.slowtest
         def test_function():
            pass
  
    will set a 'slowtest' :class:`MarkInfo` object
    on the ``test_function`` object. """

    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name)
        return MarkDecorator(name)

class MarkDecorator:
    """ A decorator for test functions and test classes.  When applied
    it will create :class:`MarkInfo` objects which may be
    :ref:`retrieved by hooks as item keywords <excontrolskip>`.
    MarkDecorator instances are often created like this::

        mark1 = py.test.mark.NAME              # simple MarkDecorator
        mark2 = py.test.mark.NAME(name1=value) # parametrized MarkDecorator

    and can then be applied as decorators to test functions::

        @mark2
        def test_function():
            pass
    """
    def __init__(self, name, args=None, kwargs=None):
        self.markname = name
        self.args = args or ()
        self.kwargs = kwargs or {}

    def __repr__(self):
        d = self.__dict__.copy()
        name = d.pop('markname')
        return "<MarkDecorator %r %r>" %(name, d)

    def __call__(self, *args, **kwargs):
        """ if passed a single callable argument: decorate it with mark info.
            otherwise add *args/**kwargs in-place to mark information. """
        if args:
            func = args[0]
            if len(args) == 1 and hasattr(func, '__call__') or \
               hasattr(func, '__bases__'):
                if hasattr(func, '__bases__'):
                    if hasattr(func, 'pytestmark'):
                        l = func.pytestmark
                        if not isinstance(l, list):
                           func.pytestmark = [l, self]
                        else:
                           l.append(self)
                    else:
                       func.pytestmark = [self]
                else:
                    holder = getattr(func, self.markname, None)
                    if holder is None:
                        holder = MarkInfo(self.markname, self.args, self.kwargs)
                        setattr(func, self.markname, holder)
                    else:
                        holder.kwargs.update(self.kwargs)
                        holder.args += self.args
                return func
        kw = self.kwargs.copy()
        kw.update(kwargs)
        args = self.args + args
        return self.__class__(self.markname, args=args, kwargs=kw)

class MarkInfo:
    """ Marking object created by :class:`MarkDecorator` instances. """
    def __init__(self, name, args, kwargs):
        #: name of attribute
        self.name = name
        #: positional argument list, empty if none specified
        self.args = args
        #: keyword argument dictionary, empty if nothing specified
        self.kwargs = kwargs

    def __repr__(self):
        return "<MarkInfo %r args=%r kwargs=%r>" % (
                self.name, self.args, self.kwargs)

def pytest_itemcollected(item):
    if not isinstance(item, pytest.Function):
        return
    try:
        func = item.obj.__func__
    except AttributeError:
        func = getattr(item.obj, 'im_func', item.obj)
    pyclasses = (pytest.Class, pytest.Module)
    for node in item.listchain():
        if isinstance(node, pyclasses):
            marker = getattr(node.obj, 'pytestmark', None)
            if marker is not None:
                if isinstance(marker, list):
                    for mark in marker:
                        mark(func)
                else:
                    marker(func)
        node = node.parent
    item.keywords.update(py.builtin._getfuncdict(func))
