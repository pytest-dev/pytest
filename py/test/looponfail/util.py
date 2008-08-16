import py
from py.__.test import event

class StatRecorder:
    def __init__(self, rootdirlist):
        self.rootdirlist = rootdirlist
        self.statcache = {}
        self.check() # snapshot state

    def fil(self, p): 
        return p.ext in ('.py', '.txt', '.c', '.h')
    def rec(self, p):
        return p.check(dotfile=0)

    def waitonchange(self, checkinterval=1.0):
        while 1:
            changed = self.check()
            if changed:
                return
            py.std.time.sleep(checkinterval)

    def check(self, removepycfiles=True):
        changed = False
        statcache = self.statcache
        newstat = {}
        for rootdir in self.rootdirlist:
            for path in rootdir.visit(self.fil, self.rec):
                oldstat = statcache.get(path, None)
                if oldstat is not None:
                    del statcache[path]
                try:
                    newstat[path] = curstat = path.stat()
                except py.error.ENOENT:
                    if oldstat:
                        del statcache[path]
                        changed = True
                else:
                    if oldstat:
                       if oldstat.mtime != curstat.mtime or \
                          oldstat.size != curstat.size:
                            changed = True
                            print "# MODIFIED", path
                            if removepycfiles and path.ext == ".py":
                                pycfile = path + "c"
                                if pycfile.check():
                                    pycfile.remove()
                                
                    else:
                        changed = True
        if statcache:
            changed = True
        self.statcache = newstat
        return changed


class EventRecorder(object):
    def __init__(self, bus):
        self.events = []
        self.bus = bus
        self.bus.subscribe(self.events.append)

    def getfailures(self):
        return [ev for ev in self.events 
                    if isinstance(ev, event.BaseReport) and \
                       ev.failed]
    def clear(self):
        self.events[:] = []

    def unsubscribe(self):
        self.bus.unsubscribe(self.events.append)
