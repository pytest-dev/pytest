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

Marking classes or modules 
----------------------------------------------------

To mark all methods of a class set a ``pytestmark`` attribute like this::

    import py

    class TestClass:
        pytestmark = py.test.mark.webtest

You can re-use the same markers that you would use for decorating
a function - in fact this marker decorator will be applied
to all test methods of the class. 

You can also set a module level marker::

    import py
    pytestmark = py.test.mark.webtest

in which case then the marker decorator will be applied to all functions and 
methods defined in the module.  

The order in which marker functions are called is this::

    per-function (upon import of module already) 
    per-class
    per-module 

Later called markers may overwrite previous key-value settings. 
Positional arguments are all appended to the same 'args' list 
of the Marker object. 

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
            if len(args) == 1 and hasattr(args[0], '__call__'):
                func = args[0]
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
            if isinstance(marker, MarkDecorator):
                marker(func)
    return item
