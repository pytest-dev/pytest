""" 
    test collection and execution events 
"""

import py
import time
from py.__.test.outcome import Skipped

class BaseEvent(object):
    def __repr__(self):
        l = ["%s=%s" %(key, value)
           for key, value in self.__dict__.items()]
        return "<%s %s>" %(self.__class__.__name__, " ".join(l),)

class NOP(BaseEvent):
    pass

# ----------------------------------------------------------------------
# Events related to collecting and executing test Items 
# ----------------------------------------------------------------------

class BaseReport(BaseEvent):
    def toterminal(self, out):
        longrepr = self.longrepr 
        if hasattr(longrepr, 'toterminal'):
            longrepr.toterminal(out)
        else:
            out.line(str(longrepr))
   
class ItemTestReport(BaseReport):
    """ Test Execution Report. """
    failed = passed = skipped = False

    def __init__(self, colitem, excinfo=None, when=None, outerr=None):
        self.colitem = colitem 
        if colitem and when != "setup":
            self.keywords = colitem.readkeywords() 
        else:
            # if we fail during setup it might mean 
            # we are not able to access the underlying object
            # this might e.g. happen if we are unpickled 
            # and our parent collector did not collect us 
            # (because it e.g. skipped for platform reasons)
            self.keywords = {}  
        if not excinfo:
            self.passed = True
            self.shortrepr = "." 
        else:
            self.when = when 
            if not isinstance(excinfo, py.code.ExceptionInfo):
                self.failed = True
                shortrepr = "?"
                longrepr = excinfo 
            elif excinfo.errisinstance(Skipped):
                self.skipped = True 
                shortrepr = "s"
                longrepr = self.colitem._repr_failure_py(excinfo, outerr)
            else:
                self.failed = True
                shortrepr = self.colitem.shortfailurerepr
                if self.when == "execute":
                    longrepr = self.colitem.repr_failure(excinfo, outerr)
                else: # exception in setup or teardown 
                    longrepr = self.colitem._repr_failure_py(excinfo, outerr)
                    shortrepr = shortrepr.lower()
            self.shortrepr = shortrepr 
            self.longrepr = longrepr 
            

class CollectionReport(BaseReport):
    """ Collection Report. """
    skipped = failed = passed = False 

    def __init__(self, colitem, result, excinfo=None, when=None, outerr=None):
        self.colitem = colitem 
        if not excinfo:
            self.passed = True
            self.result = result 
        else:
            self.when = when 
            self.outerr = outerr
            self.longrepr = self.colitem._repr_failure_py(excinfo, outerr)
            if excinfo.errisinstance(Skipped):
                self.skipped = True
                self.reason = str(excinfo.value)
            else:
                self.failed = True

    def toterminal(self, out):
        longrepr = self.longrepr 
        if hasattr(longrepr, 'toterminal'):
            longrepr.toterminal(out)
        else:
            out.line(str(longrepr))

class LooponfailingInfo(BaseEvent):
    def __init__(self, failreports, rootdirs):
        self.failreports = failreports
        self.rootdirs = rootdirs

# make all eventclasses available on BaseEvent so that
# consumers of events can easily filter by 
# 'isinstance(event, event.Name)' checks

for name, cls in vars().items():
    if hasattr(cls, '__bases__') and issubclass(cls, BaseEvent):
        setattr(BaseEvent, name, cls)
#
