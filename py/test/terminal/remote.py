from __future__ import generators
import py
from py.__.test.terminal.out import getout 
import sys

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

class FailingCollector(py.test.collect.Collector):
    def __init__(self, faileditems):
        self._faileditems = faileditems

    def __iter__(self):
        for x in self._faileditems:
            yield x

def waitfinish(channel):
    try:
        while 1:
            try:
                channel.waitclose(0.1)
            except (IOError, py.error.Error):
                continue
            else:
                return channel.receive()
    finally:
        #print "closing down channel and gateway"
        channel.gateway.exit()

def failure_slave(channel):
    """ we run this on the other side. """
    args, failures = channel.receive()
    config = py.test.config._reparse(args) 
    # making this session definitely non-remote 
    config.option.executable = py.std.sys.executable 
    config.option.looponfailing = False 
    config.option._remote = False 
    config.option._fromremote = True 
    if failures: 
        cols = getfailureitems(failures)
    else:
        cols = args 
    #print "processing", cols
    session = config.getsessionclass()(config) 
    session.shouldclose = channel.isclosed 
    failures = session.main()
    channel.send(failures)

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

def failure_master(executable, out, args, failures):
    gw = py.execnet.PopenGateway(executable) 
    channel = gw.remote_exec("""
        from py.__.test.terminal.remote import failure_slave
        failure_slave(channel) 
    """, stdout=out, stderr=out) 
    channel.send((args, failures))
    return waitfinish(channel)

def generalize(p1, p2): 
    general = p1 
    for x, y in zip(p1.parts(), p2.parts()): 
        if x != y: 
            break 
        general = x 
    return general 

def getrootdir(args): 
    tops = []
    for arg in args: 
        p = py.path.local(arg)
        tops.append(p.pypkgpath() or p)
    p = reduce(generalize, tops) 
    if p.check(file=1): 
        p = p.dirpath()
    return p 

def main(config, file, args): 
    """ testing process and output happens at a remote place. """ 
    assert file  
    if hasattr(file, 'write'): 
        def out(data): 
            file.write(data) 
            file.flush() 
    else: 
        out = file 
    failures = []
    args = list(args)
    rootdir = getrootdir(config.remaining) 
    #print "rootdir", rootdir
    wasfailing = False 
    while 1:
        if config.option.looponfailing and (failures or not wasfailing): 
            while not checkpyfilechange(rootdir):
                py.std.time.sleep(0.4)
        wasfailing = len(failures)
        failures = failure_master(config.option.executable, out, args, failures)
        if not config.option.looponfailing: 
            break
        print "#" * 60
        print "# looponfailing: mode: %d failures remaining" % len(failures)
        for root, names in failures:
            name = "/".join(names) # XXX
            print "Failure at: %r" % (name,) 
        print "#    watching py files below %s" % rootdir
        print "#                           ", "^" * len(str(rootdir))
    return failures

