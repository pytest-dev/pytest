from py.__.test import event
from py.__.test.collect import getrelpath

import sys

class BaseReporter(object):
    def __init__(self, bus=None):
        self._reset()
        self._bus = bus
        if bus:
            self._bus.subscribe(self.processevent)

    def _reset(self):
        self._passed = []
        self._skipped = []
        self._failed = []
        self._deselected = []

    def deactivate(self):
        if self._bus:
            self._bus.unsubscribe(self.processevent)

    def processevent(self, ev):
        evname = ev.__class__.__name__ 
        repmethod = getattr(self, "rep_%s" % evname, None)
        if repmethod is None:
            self.rep(ev)
        else:
            repmethod(ev)

    def rep(self, ev):
        pass

    def rep_ItemTestReport(self, ev):
        if ev.skipped:
            self._skipped.append(ev)
        elif ev.failed:
            self._failed.append(ev)
        elif ev.passed:
            self._passed.append(ev)

    def rep_CollectionReport(self, ev):
        if ev.skipped:
            self._skipped.append(ev)
        elif ev.failed:
            self._failed.append(ev)
        else:
            pass # don't record passed collections 

    def rep_TestrunStart(self, ev):
        self._reset()

    def rep_Deselected(self, ev):
        self._deselected.extend(ev.items)

    def _folded_skips(self):
        d = {}
        for event in self._skipped:
            longrepr = event.outcome.longrepr
            key = longrepr.path, longrepr.lineno, longrepr.message
            d.setdefault(key, []).append(event)
        l = []
        for key, events in d.iteritems(): 
            l.append((len(events),) + key)
        return l 

def repr_pythonversion(v=None):
    if v is None:
        v = sys.version_info
    try:
        return "%s.%s.%s-%s-%s" % v
    except (TypeError, ValueError):
        return str(v)

