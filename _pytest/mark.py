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

    group._addoption("-m",
        action="store", dest="markexpr", default="", metavar="MARKEXPR",
        help="only run tests matching given mark expression.  "
             "example: -m 'mark1 and not mark2'."
             )

    group.addoption("--markers", action="store_true", help=
        "show markers (builtin, plugin and per-project ones).")

    parser.addini("markers", "markers for test functions", 'linelist')

def pytest_cmdline_main(config):
    if config.option.markers:
        config.pluginmanager.do_configure(config)
        tw = py.io.TerminalWriter()
        for line in config.getini("markers"):
            name, rest = line.split(":", 1)
            tw.write("@pytest.mark.%s:" %  name, bold=True)
            tw.line(rest)
            tw.line()
        config.pluginmanager.do_unconfigure(config)
        return 0
pytest_cmdline_main.tryfirst = True

def pytest_collection_modifyitems(items, config):
    keywordexpr = config.option.keyword
    matchexpr = config.option.markexpr
    if not keywordexpr and not matchexpr:
        return
    selectuntil = False
    if keywordexpr[-1:] == ":":
        selectuntil = True
        keywordexpr = keywordexpr[:-1]

    remaining = []
    deselected = []
    for colitem in items:
        if keywordexpr and skipbykeyword(colitem, keywordexpr):
            deselected.append(colitem)
        else:
            if selectuntil:
                keywordexpr = None
            if matchexpr:
                if not matchmark(colitem, matchexpr):
                    deselected.append(colitem)
                    continue
            remaining.append(colitem)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining

class BoolDict:
    def __init__(self, mydict):
        self._mydict = mydict
    def __getitem__(self, name):
        return name in self._mydict

def matchmark(colitem, matchexpr):
    return eval(matchexpr, {}, BoolDict(colitem.obj.__dict__))

def pytest_configure(config):
    if config.option.strict:
        pytest.mark._config = config

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
        if hasattr(self, '_config'):
            self._check(name)
        return MarkDecorator(name)

    def _check(self, name):
        try:
            if name in self._markers:
                return
        except AttributeError:
            pass
        self._markers = l = set()
        for line in self._config.getini("markers"):
            beginning = line.split(":", 1)
            x = beginning[0].split("(", 1)[0]
            l.add(x)
        if name not in self._markers:
            raise AttributeError("%r not a registered marker" % (name,))

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
                        holder.add(self.args, self.kwargs)
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
        self._arglist = [(args, kwargs.copy())]

    def __repr__(self):
        return "<MarkInfo %r args=%r kwargs=%r>" % (
                self.name, self.args, self.kwargs)

    def add(self, args, kwargs):
        """ add a MarkInfo with the given args and kwargs. """
        self._arglist.append((args, kwargs))
        self.args += args
        self.kwargs.update(kwargs)

    def __iter__(self):
        """ yield MarkInfo objects each relating to a marking-call. """
        for args, kwargs in self._arglist:
            yield MarkInfo(self.name, args, kwargs)

