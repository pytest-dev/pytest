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
    """ non-underscore attributes of this object can be used as decorators for
    marking test functions. Example: @py.test.mark.slowtest in front of a
    function will set the 'slowtest' marker object on it. """
    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name)
        return MarkDecorator(name)

class MarkDecorator:
    """ decorator for setting function attributes. """
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
    def __init__(self, name, args, kwargs):
        self._name = name
        self.args = args
        self.kwargs = kwargs

    def __getattr__(self, name):
        if name[0] != '_' and name in self.kwargs:
            py.log._apiwarn("1.1", "use .kwargs attribute to access key-values")
            return self.kwargs[name]
        raise AttributeError(name)

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
