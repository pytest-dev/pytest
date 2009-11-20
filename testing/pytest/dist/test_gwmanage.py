""" 
    tests for 
    - gateway management 
    - manage rsyncing of hosts 

"""

import py
import os
from py.impl.test.dist.gwmanage import GatewayManager, HostRSync
from py.plugin import hookspec
import execnet

def pytest_funcarg__hookrecorder(request):
    _pytest = request.getfuncargvalue('_pytest')
    hook = request.getfuncargvalue('hook')
    return _pytest.gethookrecorder(hook._hookspecs, hook._registry)

def pytest_funcarg__hook(request):
    registry = py._com.Registry()
    return py._com.HookRelay(hookspec, registry)

class TestGatewayManagerPopen:
    def test_popen_no_default_chdir(self, hook):
        gm = GatewayManager(["popen"], hook)
        assert gm.specs[0].chdir is None

    def test_default_chdir(self, hook):
        l = ["ssh=noco", "socket=xyz"]
        for spec in GatewayManager(l, hook).specs:
            assert spec.chdir == "pyexecnetcache"
        for spec in GatewayManager(l, hook, defaultchdir="abc").specs:
            assert spec.chdir == "abc"
        
    def test_popen_makegateway_events(self, hook, hookrecorder, _pytest):
        hm = GatewayManager(["popen"] * 2, hook)
        hm.makegateways()
        call = hookrecorder.popcall("pytest_gwmanage_newgateway")
        assert call.gateway.spec == execnet.XSpec("popen")
        assert call.gateway.id == "1"
        assert call.platinfo.executable == call.gateway._rinfo().executable
        call = hookrecorder.popcall("pytest_gwmanage_newgateway")
        assert call.gateway.id == "2" 
        assert len(hm.group) == 2
        hm.exit()
        assert not len(hm.group) 

    def test_popens_rsync(self, hook, mysetup):
        source = mysetup.source
        hm = GatewayManager(["popen"] * 2, hook)
        hm.makegateways()
        assert len(hm.group) == 2
        for gw in hm.group:
            gw.remote_exec = None
        l = []
        hm.rsync(source, notify=lambda *args: l.append(args))
        assert not l
        hm.exit()
        assert not len(hm.group) 

    def test_rsync_popen_with_path(self, hook, mysetup):
        source, dest = mysetup.source, mysetup.dest 
        hm = GatewayManager(["popen//chdir=%s" %dest] * 1, hook)
        hm.makegateways()
        source.ensure("dir1", "dir2", "hello")
        l = []
        hm.rsync(source, notify=lambda *args: l.append(args))
        assert len(l) == 1
        assert l[0] == ("rsyncrootready", hm.group['1'].spec, source)
        hm.exit()
        dest = dest.join(source.basename)
        assert dest.join("dir1").check()
        assert dest.join("dir1", "dir2").check()
        assert dest.join("dir1", "dir2", 'hello').check()

    def test_rsync_same_popen_twice(self, hook, mysetup, hookrecorder):
        source, dest = mysetup.source, mysetup.dest 
        hm = GatewayManager(["popen//chdir=%s" %dest] * 2, hook)
        hm.makegateways()
        source.ensure("dir1", "dir2", "hello")
        hm.rsync(source)
        call = hookrecorder.popcall("pytest_gwmanage_rsyncstart") 
        assert call.source == source 
        assert len(call.gateways) == 1
        assert call.gateways[0] in hm.group
        call = hookrecorder.popcall("pytest_gwmanage_rsyncfinish") 

class pytest_funcarg__mysetup:
    def __init__(self, request):
        tmp = request.getfuncargvalue('tmpdir')
        self.source = tmp.mkdir("source")
        self.dest = tmp.mkdir("dest")
        request.getfuncargvalue("_pytest") # to have patching of py._com.comregistry

class TestHRSync:
    def test_hrsync_filter(self, mysetup):
        source, dest = mysetup.source, mysetup.dest
        source.ensure("dir", "file.txt")
        source.ensure(".svn", "entries")
        source.ensure(".somedotfile", "moreentries")
        source.ensure("somedir", "editfile~")
        syncer = HostRSync(source)
        l = list(source.visit(rec=syncer.filter,
                                   fil=syncer.filter))
        assert len(l) == 3
        basenames = [x.basename for x in l]
        assert 'dir' in basenames
        assert 'file.txt' in basenames
        assert 'somedir' in basenames

    def test_hrsync_one_host(self, mysetup):
        source, dest = mysetup.source, mysetup.dest
        gw = execnet.makegateway("popen//chdir=%s" % dest)
        finished = []
        rsync = HostRSync(source)
        rsync.add_target_host(gw, finished=lambda: finished.append(1))
        source.join("hello.py").write("world")
        rsync.send()
        gw.exit()
        assert dest.join(source.basename, "hello.py").check()
        assert len(finished) == 1
