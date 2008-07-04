import py

from inspect import isclass, ismodule
from py.__.test.outcome import Skipped, Failed, Passed
from py.__.test.collect import FunctionMixin

_dummy = object()

class SetupState(object):
    """ shared state for setting up/tearing down tests. """
    def __init__(self):
        self.stack = []

    def teardown_all(self): 
        while self.stack: 
            col = self.stack.pop() 
            col.teardown() 
     
    def prepare(self, colitem): 
        """ setup objects along the collector chain to the test-method
            Teardown any unneccessary previously setup objects. 
        """
        needed_collectors = colitem.listchain() 
        while self.stack: 
            if self.stack == needed_collectors[:len(self.stack)]: 
                break 
            col = self.stack.pop() 
            col.teardown()
        for col in needed_collectors[len(self.stack):]: 
            #print "setting up", col
            col.setup() 
            self.stack.append(col) 

class Item(py.test.collect.Collector): 
    def startcapture(self): 
        self._config._startcapture(self, path=self.fspath)

    def finishcapture(self): 
        self._config._finishcapture(self)

class Function(FunctionMixin, Item): 
    """ a Function Item is responsible for setting up  
        and executing a Python callable test object.
    """
    _state = SetupState()
    def __init__(self, name, parent, args=(), obj=_dummy, sort_value = None):
        super(Function, self).__init__(name, parent) 
        self._args = args
        if obj is not _dummy: 
            self._obj = obj 
        self._sort_value = sort_value
        
    def __repr__(self): 
        return "<%s %r>" %(self.__class__.__name__, self.name)

    def _getsortvalue(self):  
        if self._sort_value is None:
            return self._getpathlineno()
        return self._sort_value

    def run(self):
        """ setup and execute the underlying test function. """
        self._state.prepare(self) 
        self.execute(self.obj, *self._args)

    def execute(self, target, *args):
        """ execute the given test function. """
        target(*args)

#
# triggering specific outcomes while executing Items
#
class BaseReason(object):
    def __init__(self, msg="unknown reason", **kwds):
        self.msg = msg
        self.__dict__.update(kwds)

    def __repr__(self):
        return self.msg

# whatever comes here....

def skip(msg=BaseReason()):
    """ skip with the given Message. """
    __tracebackhide__ = True
    raise Skipped(msg=msg) 

def fail(msg="unknown failure"):
    """ fail with the given Message. """
    __tracebackhide__ = True
    raise Failed(msg=msg) 

