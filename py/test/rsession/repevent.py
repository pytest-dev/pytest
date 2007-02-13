""" Reporter classes for showing asynchronous and synchronous status events
"""

import py
import time

def basic_report(msg_type, message):
    print msg_type, message

#def report(msg_type, message):
#    pass

##def report_error(excinfo):
##    if isinstance(excinfo, py.test.collect.Item.Skipped):
##        # we need to dispatch this info
##        report(Skipped(excinfo))
##    else:
##        report("itererror", excinfo)

def wrapcall(reporter, func, *args, **kwargs):
    reporter(CallStart(func, args, kwargs))
    try:
        retval = func(*args, **kwargs)
    except:
        reporter(CallException(func, args, kwargs))
        raise
    else:
        reporter(CallFinish(func, args, kwargs))
        return retval

# ----------------------------------------------------------------------
# Reporting Events 
# ----------------------------------------------------------------------

class ReportEvent(object):
    def __repr__(self):
        l = ["%s=%s" %(key, value)
           for key, value in self.__dict__.items()]
        return "<%s %s>" %(self.__class__.__name__, " ".join(l),)

class SendItem(ReportEvent):
    def __init__(self, channel, item):
        self.item = item
        self.channel = channel
        if channel:
            self.host = channel.gateway.host

class ReceivedItemOutcome(ReportEvent):
    def __init__(self, channel, item, outcome):
        self.channel = channel
        if channel:
            self.host = channel.gateway.host
        self.item = item
        self.outcome = outcome

class CallEvent(ReportEvent):
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def __repr__(self):
        call = "%s args=%s, kwargs=%s" %(self.func.__name__, 
                                         self.args, self.kwargs)
        return '<%s %s>' %(self.__class__.__name__, call)

class CallStart(CallEvent):
    pass

class CallException(CallEvent):
    pass

class CallFinish(CallEvent):
    pass

class HostRSyncing(ReportEvent):
    def __init__(self, host, root, remotepath, synced):
        self.host = host
        self.root = root
        self.remotepath = remotepath
        self.synced = synced

class HostGatewayReady(ReportEvent):
    def __init__(self, host, roots):
        self.host = host
        self.roots = roots

class HostRSyncRootReady(ReportEvent):
    def __init__(self, host, root):
        self.host = host
        self.root = root

class TestStarted(ReportEvent):
    def __init__(self, hosts, topdir, roots):
        self.hosts = hosts
        self.topdir = topdir
        self.roots = roots
        self.timestart = time.time()

class TestFinished(ReportEvent):
    def __init__(self):
        self.timeend = time.time()

class Nodes(ReportEvent):
    def __init__(self, nodes):
        self.nodes = nodes

class SkippedTryiter(ReportEvent):
    def __init__(self, excinfo, item):
        self.excinfo = excinfo
        self.item = item

class FailedTryiter(ReportEvent):
    def __init__(self, excinfo, item):
        self.excinfo = excinfo
        self.item = item

class ItemStart(ReportEvent):
    """ This class shows most of the start stuff, like directory, module, class
    can be used for containers
    """
    def __init__(self, item):
        self.item = item

class RsyncFinished(ReportEvent):
    def __init__(self):
        self.time = time.time()

class ImmediateFailure(ReportEvent):
    def __init__(self, item, outcome):
        self.item = item
        self.outcome = outcome

class PongReceived(ReportEvent):
    def __init__(self, hostid, result):
        self.hostid = hostid
        self.result = result

class InterruptedExecution(ReportEvent):
    def __init__(self):
        self.timeend = time.time()

class CrashedExecution(ReportEvent):
    def __init__(self):
        self.timeend = time.time()
