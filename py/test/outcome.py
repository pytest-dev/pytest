
""" File defining possible outcomes of running
"""

class Outcome: 
    def __init__(self, msg=None, excinfo=None): 
        self.msg = msg 
        self.excinfo = excinfo

    def __repr__(self):
        if self.msg: 
            return repr(self.msg) 
        return "<%s instance>" %(self.__class__.__name__,)
    __str__ = __repr__

class Passed(Outcome): 
    pass

class Failed(Outcome): 
    pass

class ExceptionFailure(Failed): 
    def __init__(self, expr, expected, msg=None, excinfo=None): 
        Failed.__init__(self, msg=msg, excinfo=excinfo) 
        self.expr = expr 
        self.expected = expected

class Skipped(Outcome): 
    pass
