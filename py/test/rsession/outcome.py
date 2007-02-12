
""" Classes for representing outcomes on master and slavenode sides
"""

# WARNING! is_critical is debugging flag which means something
#          wrong went on a different level. Usually that means
#          internal bug.

import sys
import py

class Outcome(object):
    def __init__(self, setupfailure=False, excinfo=None, skipped=None,
            is_critical=False):
        self.passed = not excinfo and not skipped
        self.skipped = skipped 
        self.setupfailure = setupfailure 
        self.excinfo = excinfo
        self.is_critical = is_critical
        self.signal = 0
        self.stdout = "" # XXX temporary
        self.stderr = ""
        assert bool(self.passed) + bool(excinfo) + bool(skipped) == 1
    
    def make_excinfo_repr(self, tbstyle):
        if self.excinfo is None:
            return None
        excinfo = self.excinfo
        tb_info = [self.traceback_entry_repr(x, tbstyle)
                   for x in excinfo.traceback]
        rec_index = excinfo.traceback.recursionindex()
        if hasattr(excinfo, 'type'):
            etype = excinfo.type
            if hasattr(etype, '__name__'):
                etype = etype.__name__
        else:
            etype = excinfo.typename
        val = getattr(excinfo, 'value', None)
        if not val:
            val = excinfo.exconly()
        val = str(val)
        return (etype, val, (tb_info, rec_index))
    
    def traceback_entry_repr(self, tb_entry, tb_style):
        lineno = tb_entry.lineno
        relline = lineno - tb_entry.frame.code.firstlineno
        path = str(tb_entry.path)
        #try:
        try:
            if tb_style == 'long':
                source = str(tb_entry.getsource())
            else:
                source = str(tb_entry.getsource()).split("\n")[relline]
        except py.error.ENOENT:
            source = "[cannot get source]"
        name = str(tb_entry.frame.code.name)
        # XXX: Bare except. What can getsource() raise anyway?
        # SyntaxError, AttributeError, IndentationError for sure, check it
        #except:
        #    source = "<could not get source>"
        return (relline, lineno, source, path, name)
        
    def make_repr(self, tbstyle="long"):
        return (self.passed, self.setupfailure, 
                self.make_excinfo_repr(tbstyle), 
                self.skipped, self.is_critical, 0, self.stdout, self.stderr)

class TracebackEntryRepr(object):
    def __init__(self, tbentry):
        relline, lineno, self.source, self.path, self.name = tbentry
        self.relline = int(relline)
        self.path = py.path.local(self.path)
        self.lineno = int(lineno)
        self.locals = {}
    
    def __repr__(self):
        return "line %s in %s\n  %s" %(self.lineno, self.path, self.source[100:])

    def getsource(self):
        return py.code.Source(self.source).strip()

    def getfirstlinesource(self):
        return self.lineno - self.relline

class TracebackRepr(list):
    def recursionindex(self):
        return self.recursion_index

class ExcInfoRepr(object):
    def __init__(self, excinfo):
        self.typename, self.value, tb_i = excinfo
        tb, rec_index = tb_i
        self.traceback = TracebackRepr([TracebackEntryRepr(x) for x in tb])
        self.traceback.recursion_index = rec_index
    
    def __repr__(self):
        l = ["%s=%s" %(x, getattr(self, x))
                for x in "typename value traceback".split()]
        return "<ExcInfoRepr %s>" %(" ".join(l),)

    def exconly(self, tryshort=False):
        """ Somehow crippled version of original one
        """
        return "%s: %s" % (self.typename, self.value)

    def errisinstance(self, exc_t):
        if not isinstance(exc_t, tuple):
            exc_t = (exc_t,)
        for exc in exc_t:
            if self.typename == str(exc).split('.')[-1]:
                return True
        return False

class ReprOutcome(object):
    def __init__(self, repr_tuple):
        (self.passed, self.setupfailure, excinfo, self.skipped,
         self.is_critical, self.signal, self.stdout, self.stderr) = repr_tuple
        if excinfo is None:
            self.excinfo = None
        else:
            self.excinfo = ExcInfoRepr(excinfo)

    def __repr__(self):
        l = ["%s=%s" %(x, getattr(self, x))
                for x in "signal passed skipped setupfailure excinfo stdout stderr".split()]
        return "<ReprOutcome %s>" %(" ".join(l),)
