from __future__ import generators
import sys
import py

class ExceptionInfo(object):
    """ wraps sys.exc_info() objects and offers
        help for navigating the traceback.
    """
    _striptext = '' 
    def __init__(self, tup=None, exprinfo=None):
        # NB. all attributes are private!  Subclasses or other
        #     ExceptionInfo-like classes may have different attributes.
        if tup is None:
            tup = sys.exc_info()
            if exprinfo is None and isinstance(tup[1], py.magic.AssertionError):
                exprinfo = tup[1].msg
                if exprinfo and exprinfo.startswith('assert '):
                    self._striptext = 'AssertionError: '
        self._excinfo = tup
        self.type, self.value, tb = self._excinfo
        self.typename = str(self.type)
        self.traceback = py.code.Traceback(tb) 

    def exconly(self, tryshort=False): 
        lines = py.std.traceback.format_exception_only(self.type, self.value)
        text = ''.join(lines)
        if text.endswith('\n'):
            text = text[:-1]
        if tryshort: 
            if text.startswith(self._striptext): 
                text = text[len(self._striptext):]
        return text

    def errisinstance(self, exc): 
        return isinstance(self.value, exc) 

    def __str__(self):
        # XXX wrong str
        return self.exconly() 

