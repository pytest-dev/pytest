"""
mark test functions with keywords that may hold values. 

Marking functions by a decorator 
----------------------------------------------------

By default, all filename parts and class/function names of a test
function are put into the set of keywords for a given test.  You can
specify additional kewords like this::

    @py.test.mark.webtest
    def test_send_http():
        ... 

This will set an attribute 'webtest' to True on the given test function.
You can read the value 'webtest' from the functions __dict__ later.

You can also set values for an attribute which are put on an empty
dummy object::

    @py.test.mark.webtest(firefox=30)
    def test_receive():
        ...

after which ``test_receive.webtest.firefox == 30`` holds true. 

In addition to keyword arguments you can also use positional arguments::

    @py.test.mark.webtest("triangular")
    def test_receive():
        ...

after which ``test_receive.webtest._args[0] == 'triangular`` holds true.


Marking classes or modules 
----------------------------------------------------

To mark all methods of a class you can set a class-level attribute::

    class TestClass:
        pytestmark = py.test.mark.webtest

the marker function will be applied to all test methods. 

If you set a marker it inside a test module like this::

    pytestmark = py.test.mark.webtest

the marker will be applied to all functions and methods of 
that module.  The module marker is applied last.  

Outer ``pytestmark`` keywords will overwrite inner keyword 
values.   Positional arguments are all appeneded to the 
same '_args' list. 
"""
import py

def pytest_namespace():
    return {'mark': Mark()}


class Mark(object):
    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name)
        return MarkerDecorator(name)

class MarkerDecorator:
    """ decorator for setting function attributes. """
    def __init__(self, name):
        self.markname = name
        self.kwargs = {}
        self.args = []

    def __repr__(self):
        d = self.__dict__.copy()
        name = d.pop('markname')
        return "<MarkerDecorator %r %r>" %(name, d)

    def __call__(self, *args, **kwargs):
        if args:
            if len(args) == 1 and hasattr(args[0], '__call__'):
                func = args[0]
                holder = getattr(func, self.markname, None)
                if holder is None:
                    holder = MarkHolder(self.markname, self.args, self.kwargs)
                    setattr(func, self.markname, holder)
                else:
                    holder.__dict__.update(self.kwargs)
                    holder._args.extend(self.args)
                return func
            else:
                self.args.extend(args)
        self.kwargs.update(kwargs)
        return self
        
class MarkHolder:
    def __init__(self, name, args, kwargs):
        self._name = name
        self._args = args
        self._kwargs = kwargs
        self.__dict__.update(kwargs)

    def __repr__(self):
        return "<Marker %r args=%r kwargs=%r>" % (
                self._name, self._args, self._kwargs)
            

def pytest_pycollect_makeitem(__multicall__, collector, name, obj):
    item = __multicall__.execute()
    if isinstance(item, py.test.collect.Function):
        cls = collector.getparent(py.test.collect.Class)
        mod = collector.getparent(py.test.collect.Module)
        func = getattr(item.obj, 'im_func', item.obj)
        for parent in [x for x in (mod, cls) if x]:
            marker = getattr(parent.obj, 'pytestmark', None)
            if isinstance(marker, MarkerDecorator):
                marker(func)
    return item
