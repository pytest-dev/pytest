"""
mark test functions with keywords that may hold values. 

Marking functions and setting rich attributes
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

after which ``test_receive.webtest._1 == 'triangular`` hold true.

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

    def __repr__(self):
        d = self.__dict__.copy()
        name = d.pop('markname')
        return "<MarkerDecorator %r %r>" %(name, d)

    def __call__(self, *args, **kwargs):
        if args:
            if hasattr(args[0], '__call__'):
                func = args[0]
                mh = MarkHolder(getattr(self, 'kwargs', {}))
                setattr(func, self.markname, mh)
                return func
            # not a function so we memorize all args/kwargs settings
            for i, arg in enumerate(args):
                kwargs["_" + str(i)] = arg
        if hasattr(self, 'kwargs'):
            raise TypeError("double mark-keywords?")
        self.kwargs = kwargs.copy()
        return self
        
class MarkHolder:
    def __init__(self, kwargs):
        self.__dict__.update(kwargs)
