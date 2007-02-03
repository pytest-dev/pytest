import py

from inspect import isclass, ismodule
from py.__.test.outcome import Skipped, Failed, Passed

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
        if not self._config.option.nocapture:
            self._capture = py.io.StdCaptureFD() 

    def finishcapture(self): 
        if hasattr(self, '_capture'): 
            capture = self._capture 
            del self._capture
            self._captured_out, self._captured_err = capture.reset()
            

class Function(Item): 
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

    def _getpathlineno(self):
        code = py.code.Code(self.obj) 
        return code.path, code.firstlineno 

    def _getsortvalue(self):  
        if self._sort_value is None:
            return self._getpathlineno()
        return self._sort_value

    def run(self):
        self._state.prepare(self) 
        self.execute(self.obj, *self._args)

    def execute(self, target, *args):
        """ default implementation for calling a test target is to
            simply call it.
        """
        target(*args)

    def setup(self): 
        if getattr(self.obj, 'im_self', None): 
            name = 'setup_method' 
        else: 
            name = 'setup_function' 
        obj = self.parent.obj 
        meth = getattr(obj, name, None)
        if meth is not None: 
            return meth(self.obj) 

    def teardown(self): 
        if getattr(self.obj, 'im_self', None): 
            name = 'teardown_method' 
        else: 
            name = 'teardown_function' 
        obj = self.parent.obj 
        meth = getattr(obj, name, None)
        if meth is not None: 
            return meth(self.obj) 

#
# triggering specific outcomes while executing Items
#
def skip(msg="unknown reason"):
    """ skip with the given Message. """
    __tracebackhide__ = True
    raise Skipped(msg=msg) 

def fail(msg="unknown failure"):
    """ fail with the given Message. """
    __tracebackhide__ = True
    raise Failed(msg=msg) 

