""" generic mechanism for marking and selecting python functions. """
import py

def pytest_namespace():
    return {'mark': MarkGenerator()}

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('-k',
        action="store", dest="keyword", default='',
        help="only run test items matching the given "
             "space separated keywords.  precede a keyword with '-' to negate. "
             "Terminate the expression with ':' to treat a match as a signal "
             "to run all subsequent tests. ")

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
    chain = colitem.listchain()
    for key in filter(None, keywordexpr.split()):
        eor = key[:1] == '-'
        if eor:
            key = key[1:]
        if not (eor ^ matchonekeyword(key, chain)):
            return True

def matchonekeyword(key, chain):
    elems = key.split(".")
    # XXX O(n^2), anyone cares?
    chain = [item.keywords for item in chain if item.keywords]
    for start, _ in enumerate(chain):
        if start + len(elems) > len(chain):
            return False
        for num, elem in enumerate(elems):
            for keyword in chain[num + start]:
                ok = False
                if elem in keyword:
                    ok = True
                    break
            if not ok:
                break
        if num == len(elems) - 1 and ok:
            return True
    return False

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
    :ref:`retrieved by hooks as item keywords`  MarkDecorator instances 
    are usually created by writing::

        mark1 = py.test.mark.NAME              # simple MarkDecorator
        mark2 = py.test.mark.NAME(name1=value) # parametrized MarkDecorator

    and can then be applied as decorators to test functions::

        @mark2
        def test_function():
            pass
    """
    def __init__(self, name):
        self.markname = name
        self.kwargs = {}
        self.args = []

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
                        holder.args.extend(self.args)
                return func
            else:
                self.args.extend(args)
        self.kwargs.update(kwargs)
        return self

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
                self._name, self.args, self.kwargs)

def pytest_pycollect_makeitem(__multicall__, collector, name, obj):
    item = __multicall__.execute()
    if isinstance(item, py.test.collect.Function):
        cls = collector.getparent(py.test.collect.Class)
        mod = collector.getparent(py.test.collect.Module)
        func = item.obj
        func = getattr(func, '__func__', func) # py3
        func = getattr(func, 'im_func', func)  # py2
        for parent in [x for x in (mod, cls) if x]:
            marker = getattr(parent.obj, 'pytestmark', None)
            if marker is not None:
                if not isinstance(marker, list):
                    marker = [marker]
                for mark in marker:
                    if isinstance(mark, MarkDecorator):
                        mark(func)
                item.keywords.update(py.builtin._getfuncdict(func) or {})
    return item
