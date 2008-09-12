""" 
    test collection and execution events 
"""

import py
import time
from py.__.test.outcome import Skipped

class EventBus(object): 
    """ General Event Bus for distributing events. """ 
    def __init__(self):
        self._subscribers = []
    
    def subscribe(self, callback):
        """ subscribe given callback to bus events. """ 
        self._subscribers.append(callback) 

    def unsubscribe(self, callback):
        """ unsubscribe given callback from bus events. """ 
        self._subscribers.remove(callback) 
    
    def notify(self, event):
        for subscriber in self._subscribers:
            subscriber(event) 


class BaseEvent(object):
    def __repr__(self):
        l = ["%s=%s" %(key, value)
           for key, value in self.__dict__.items()]
        return "<%s %s>" %(self.__class__.__name__, " ".join(l),)

def timestamp():
    return time.time()

class NOP(BaseEvent):
    pass

# ----------------------------------------------------------------------
# Basic Live Reporting Events 
# ----------------------------------------------------------------------

class TestrunStart(BaseEvent):
    def __init__(self):
        self.timestart = time.time()

class TestrunFinish(BaseEvent):
    def __init__(self, exitstatus=0, excinfo=None):
        self.exitstatus = exitstatus
        if excinfo is None:
            self.excrepr = None
        else:
            self.excrepr = excinfo.getrepr()
        self.timeend = time.time()

class InternalException(BaseEvent):
    def __init__(self, excinfo=None):
        if excinfo is None:
            excinfo = py.code.ExceptionInfo()
        self.repr = excinfo.getrepr(funcargs=True, showlocals=True)

# ----------------------------------------------------------------------
# Events related to collecting and executing test Items 
# ----------------------------------------------------------------------

class ItemStart(BaseEvent):
    def __init__(self, item, host=None):
        self.item = item
        self.host = host
        self.time = timestamp()

class Deselected(BaseEvent):
    def __init__(self, items):
        self.items = items 
        

class BaseReport(BaseEvent):
    failed = passed = skipped = None
    def __init__(self, colitem, **kwargs):
        self.colitem = colitem 
        assert len(kwargs) == 1, kwargs
        name, value = kwargs.items()[0]
        setattr(self, name, True)
        self.outcome = value

    def toterminal(self, out):
        longrepr = self.outcome.longrepr 
        if hasattr(longrepr, 'toterminal'):
            longrepr.toterminal(out)
        else:
            out.line(str(longrepr))
    
class ItemTestReport(BaseReport):
    """ Test Execution Report. """

class CollectionStart(BaseEvent):
    def __init__(self, collector):
        self.collector = collector 

class CollectionReport(BaseReport):
    """ Collection Report. """
    def __init__(self, colitem, result, **kwargs):
        super(CollectionReport, self).__init__(colitem, **kwargs)
        self.result = result

class LooponfailingInfo(BaseEvent):
    def __init__(self, failreports, rootdirs):
        self.failreports = failreports
        self.rootdirs = rootdirs

# ----------------------------------------------------------------------
# Distributed Testing Events 
# ----------------------------------------------------------------------

class RescheduleItems(BaseEvent):
    def __init__(self, items):
        self.items = items
 
class HostGatewayReady(BaseEvent):
    def __init__(self, host, roots):
        self.host = host
        self.roots = roots

class HostUp(BaseEvent):
    def __init__(self, host, platinfo):
        self.host = host 
        self.platinfo = platinfo

class HostDown(BaseEvent):
    def __init__(self, host, error=None):
        self.host = host 
        self.error = error

# ---------------------------------------------------------------------
# Events related to rsyncing
# ---------------------------------------------------------------------

class HostRSyncing(BaseEvent):
    def __init__(self, host, root, remotepath, synced):
        self.host = host
        self.root = root
        self.remotepath = remotepath
        self.synced = synced

class RsyncFinished(BaseEvent):
    def __init__(self):
        self.time = timestamp()

class HostRSyncRootReady(BaseEvent):
    def __init__(self, host, root):
        self.host = host
        self.root = root

