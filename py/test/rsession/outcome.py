
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
        assert bool(self.passed) + bool(excinfo) + bool(skipped) == 1
    
    def make_excinfo_repr(self):
        if self.excinfo is None:
            return None
        excinfo = self.excinfo
        tb_info = [self.traceback_entry_repr(x) for x in excinfo.traceback]
        return (excinfo.type.__name__, str(excinfo.value), tb_info)
    
    def traceback_entry_repr(self, tb_entry):
        lineno = tb_entry.lineno
        relline = lineno - tb_entry.frame.code.firstlineno
        path = str(tb_entry.path)
        try:
            from py.__.test.rsession.rsession import remote_options
            if remote_options.tbstyle == 'long':
                source = str(tb_entry.getsource())
            else:
                source = str(tb_entry.getsource()).split("\n")[relline]
        except:
            source = "<could not get source>"
        return (relline, lineno, source, path)
        
    def make_repr(self):
        return (self.passed, self.setupfailure, 
                self.make_excinfo_repr(), 
                self.skipped, self.is_critical, 0, "", "")

class TracebackEntryRepr(object):
    def __init__(self, tbentry):
        relline, lineno, self.source, self.path = tbentry
        self.relline = int(relline)
        self.lineno = int(lineno)
    
    def __repr__(self):
        return "line %s in %s\n  %s" %(self.lineno, self.path, self.source[100:])

class ExcInfoRepr(object):
    def __init__(self, excinfo):
        self.typename, self.value, tb = excinfo
        self.traceback = [TracebackEntryRepr(x) for x in tb]
    
    def __repr__(self):
        l = ["%s=%s" %(x, getattr(self, x))
                for x in "typename value traceback".split()]
        return "<ExcInfoRepr %s>" %(" ".join(l),)

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
