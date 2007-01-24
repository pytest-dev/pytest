
""" simple tracer for API generation
"""

import py
import sys
import types

from py.__.apigen.tracer.description import FunctionDesc
from py.__.apigen.tracer.docstorage import DocStorage

class UnionError(Exception):
    pass

class NoValue(object):
    pass

class Tracer(object):
    """ Basic tracer object, used for gathering additional info
    about API functions
    """
    def __init__(self, docstorage):
        self.docstorage = docstorage
        self.tracing = False
    
    _locals = {}
    def _tracer(self, frame, event, arg):
        
        # perform actuall tracing
        frame = py.code.Frame(frame)
        if event == 'call':
            assert arg is None
            try:
                self.docstorage.consider_call(frame,
                                          py.code.Frame(sys._getframe(2)),
                                          self.frame)
            except ValueError:
                self.docstorage.consider_call(frame, None, self.frame)
        elif event == 'return':
            self.docstorage.consider_return(frame, arg)
        elif event == 'exception':
            self.docstorage.consider_exception(frame, arg)
        return self._tracer
    
    def start_tracing(self):
        if self.tracing:
            return
        self.tracing = True
        self.frame = py.code.Frame(sys._getframe(1))
        sys.settrace(self._tracer)
    
    def end_tracing(self):
        self.tracing = False
        sys.settrace(None)

