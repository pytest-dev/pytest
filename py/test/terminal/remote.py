from __future__ import generators
import py
from py.__.test.session import Session
from py.__.test.terminal.out import getout
from py.__.test.outcome import Failed, Passed, Skipped

def checkpyfilechange(rootdir, statcache={}):
    """ wait until project files are changed. """
    def fil(p): 
        return p.ext in ('.py', '.c', '.h')
    #fil = lambda x: x.check(fnmatch='*.py')
    def rec(p):
        return p.check(dotfile=0)
    changed = False
    for path in rootdir.visit(fil, rec):
        oldstat = statcache.get(path, None)
        try:
            statcache[path] = curstat = path.stat()
        except py.error.ENOENT:
            if oldstat:
                del statcache[path]
                print "# WARN: race condition on", path
        else:
            if oldstat:
               if oldstat.mtime != curstat.mtime or \
                  oldstat.size != curstat.size:
                    changed = True
                    print "# MODIFIED", path
            else:
                changed = True
    return changed

def getfailureitems(failures): 
    l = []
    for rootpath, names in failures:
        root = py.path.local(rootpath)
        if root.check(dir=1):
            current = py.test.collect.Directory(root).Directory(root)
        elif root.check(file=1):
            current = py.test.collect.Module(root).Module(root)
        # root is fspath of names[0] -> pop names[0]
        # slicing works with empty lists
        names = names[1:]
        while names: 
            name = names.pop(0) 
            try: 
                current = current.join(name)
            except NameError: 
                print "WARNING: could not find %s on %r" %(name, current) 
                break 
        else: 
            l.append(current) 
    return l

class RemoteTerminalSession(Session):
    def __init__(self, config, file=None):
        super(RemoteTerminalSession, self).__init__(config=config)
        self._setexecutable()
        if file is None:
            file = py.std.sys.stdout 
        self._file = file
        self.out = getout(file)

    def _setexecutable(self):
        name = self.config.option.executable
        if name is None:
            executable = py.std.sys.executable 
        else:
            executable = py.path.local.sysfind(name)
            assert executable is not None, executable 
        self.executable = executable 

    def main(self):
        rootdir = self.config.topdir 
        wasfailing = False 
        failures = []
        while 1:
            if self.config.option.looponfailing and (failures or not wasfailing): 
                while not checkpyfilechange(rootdir):
                    py.std.time.sleep(4.4)
            wasfailing = len(failures)
            failures = self.run_remote_session(failures)
            if not self.config.option.looponfailing: 
                break
            print "#" * 60
            print "# looponfailing: mode: %d failures args" % len(failures)
            for root, names in failures:
                name = "/".join(names) # XXX
                print "Failure at: %r" % (name,) 
            print "#    watching py files below %s" % rootdir
            print "#                           ", "^" * len(str(rootdir))
        return failures

    def _initslavegateway(self):
        print "* opening PopenGateway: ", self.executable 
        topdir = self.config.topdir
        return py.execnet.PopenGateway(self.executable), topdir

    def run_remote_session(self, failures):
        gw, topdir = self._initslavegateway()
        channel = gw.remote_exec("""
            from py.__.test.terminal.remote import slaverun_TerminalSession
            slaverun_TerminalSession(channel) 
        """, stdout=self.out, stderr=self.out) 
        try:
            print "MASTER: initiated slave terminal session ->"
            repr = self.config._makerepr(conftestnames=[])
            channel.send((str(topdir), repr, failures))
            print "MASTER: send start info, topdir=%s" % (topdir,)
            try:
                return channel.receive()
            except channel.RemoteError, e:
                print "*" * 70
                print "ERROR while waiting for proper slave startup"
                print "*" * 70
                print e
                return []
        finally:
            gw.exit()

def slaverun_TerminalSession(channel):
    """ we run this on the other side. """
    print "SLAVE: initializing ..."
    topdir, repr, failures = channel.receive()
    print "SLAVE: received configuration, using topdir:", topdir
    config = py.test.config 
    config._initdirect(topdir, repr, failures)
    config.option.session = None
    config.option.looponfailing = False 
    config.option.usepdb = False 
    config.option.executable = None
    if failures:
        config.option.verbose = True

    session = config.initsession()
    session.shouldclose = channel.isclosed 
    print "SLAVE: starting session.main()"
    session.main()
    failures = session.getitemoutcomepairs(Failed)
    failures = [config.get_collector_trail(item) for item,_ in failures]
    channel.send(failures)
