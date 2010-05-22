"""
generic mechanism for marking python functions. 

By using the ``py.test.mark`` helper you can instantiate
decorators that will set named meta data on test functions. 

Marking a single function 
----------------------------------------------------

You can "mark" a test function with meta data like this::

    @py.test.mark.webtest
    def test_send_http():
        ... 

This will set a "Marker" instance as a function attribute named "webtest". 
You can also specify parametrized meta data like this::

    @py.test.mark.webtest(firefox=30)
    def test_receive():
        ...

The named marker can be accessed like this later::

    test_receive.webtest.kwargs['firefox'] == 30

In addition to set key-value pairs you can also use positional arguments::

    @py.test.mark.webtest("triangular")
    def test_receive():
        ...

and later access it with ``test_receive.webtest.args[0] == 'triangular``.

.. _`scoped-marking`:

Marking whole classes or modules 
----------------------------------------------------

If you are programming with Python2.6 you may use ``py.test.mark`` decorators
with classes to apply markers to all its test methods::

    @py.test.mark.webtest
    class TestClass:
        def test_startup(self):
            ...
        def test_startup_and_more(self):
            ...

This is equivalent to directly applying the decorator to the
two test functions. 

To remain compatible with Python2.5 you can also set a 
``pytestmark`` attribute on a TestClass like this::

    import py

    class TestClass:
        pytestmark = py.test.mark.webtest

or if you need to use multiple markers you can use a list::

    import py

    class TestClass:
        pytestmark = [py.test.mark.webtest, pytest.mark.slowtest]

You can also set a module level marker::

    import py
    pytestmark = py.test.mark.webtest

in which case it will be applied to all functions and 
methods defined in the module.  

Using "-k MARKNAME" to select tests
----------------------------------------------------

You can use the ``-k`` command line option to select
tests::

    py.test -k webtest  # will only run tests marked as webtest

"""
import py

def pytest_namespace():
    return {'mark': MarkGenerator()}

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
    return item
