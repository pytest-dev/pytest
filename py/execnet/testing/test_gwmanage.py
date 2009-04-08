""" 
    tests for 
    - gateway management 
    - manage rsyncing of hosts 

"""

import py
from py.__.execnet.gwmanage import GatewayManager, HostRSync

class TestGatewayManagerPopen:
    def test_popen_no_default_chdir(self):
        gm = GatewayManager(["popen"])
        assert gm.specs[0].chdir is None

    def test_default_chdir(self):
        l = ["ssh=noco", "socket=xyz"]
        for spec in GatewayManager(l).specs:
            assert spec.chdir == "pyexecnetcache"
        for spec in GatewayManager(l, defaultchdir="abc").specs:
            assert spec.chdir == "abc"
        
    def test_popen_makegateway_events(self, _pytest):
        rec = _pytest.getcallrecorder(py.execnet._API)
        hm = GatewayManager(["popen"] * 2)
        hm.makegateways()
        call = rec.popcall("pyexecnet_gwmanage_newgateway")
        assert call.gateway.id == "[1]" 
        assert call.platinfo.executable == call.gateway._rinfo().executable
        call = rec.popcall("pyexecnet_gwmanage_newgateway")
        assert call.gateway.id == "[2]" 
        assert len(hm.gateways) == 2
        hm.exit()
        assert not len(hm.gateways) 

    def test_popens_rsync(self, source):
        hm = GatewayManager(["popen"] * 2)
        hm.makegateways()
        assert len(hm.gateways) == 2
        for gw in hm.gateways:
            gw.remote_exec = None
        l = []
        hm.rsync(source, notify=lambda *args: l.append(args))
        assert not l
        hm.exit()
        assert not len(hm.gateways) 

    def test_rsync_popen_with_path(self, source, dest):
        hm = GatewayManager(["popen//chdir=%s" %dest] * 1)
        hm.makegateways()
        source.ensure("dir1", "dir2", "hello")
        l = []
        hm.rsync(source, notify=lambda *args: l.append(args))
        assert len(l) == 1
        assert l[0] == ("rsyncrootready", hm.gateways[0].spec, source)
        hm.exit()
        dest = dest.join(source.basename)
        assert dest.join("dir1").check()
        assert dest.join("dir1", "dir2").check()
        assert dest.join("dir1", "dir2", 'hello').check()

    def test_hostmanage_rsync_same_popen_twice(self, source, dest, _pytest):
        rec = _pytest.getcallrecorder(py.execnet._API)
        hm = GatewayManager(["popen//chdir=%s" %dest] * 2)
        hm.makegateways()
        source.ensure("dir1", "dir2", "hello")
        hm.rsync(source)
        call = rec.popcall("pyexecnet_gwmanage_rsyncstart") 
        assert call.source == source 
        assert len(call.gateways) == 1
        assert hm.gateways[0] == call.gateways[0]
        call = rec.popcall("pyexecnet_gwmanage_rsyncfinish") 

    def test_multi_chdir_popen_with_path(self, testdir):
        import os
        hm = GatewayManager(["popen//chdir=hello"] * 2)
        testdir.tmpdir.chdir()
        hellopath = testdir.tmpdir.mkdir("hello").realpath()
        hm.makegateways()
        l = hm.multi_exec("import os ; channel.send(os.getcwd())").receive_each()
        paths = [x[1] for x in l]
        assert l == [str(hellopath)] * 2
        py.test.raises(hm.RemoteError, 'hm.multi_chdir("world", inplacelocal=False)')
        worldpath = hellopath.mkdir("world")
        hm.multi_chdir("world", inplacelocal=False)
        l = hm.multi_exec("import os ; channel.send(os.getcwd())").receive_each()
        assert len(l) == 2
        assert l[0] == l[1]
        curwd = os.getcwd()
        assert l[0].startswith(curwd)
        assert l[0].endswith("world")

    def test_multi_chdir_popen(self, testdir):
        import os
        hm = GatewayManager(["popen"] * 2)
        testdir.tmpdir.chdir()
        hellopath = testdir.tmpdir.mkdir("hello")
        hm.makegateways()
        hm.multi_chdir("hello", inplacelocal=False)
        l = hm.multi_exec("import os ; channel.send(os.getcwd())").receive_each()
        assert len(l) == 2
        curwd = os.path.realpath(os.getcwd())
        assert l == [curwd] * 2

        hm.multi_chdir("hello")
        l = hm.multi_exec("import os ; channel.send(os.getcwd())").receive_each()
        assert len(l) == 2
        assert l[0] == l[1]
        assert l[0].startswith(curwd)
        assert l[0].endswith("hello")

def pytest_funcarg__source(pyfuncitem):
    return py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("source")
def pytest_funcarg__dest(pyfuncitem):
    return py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("dest")

class TestHRSync:
    def test_hrsync_filter(self, source, dest):
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

    def test_hrsync_one_host(self, source, dest):
        gw = py.execnet.makegateway("popen//chdir=%s" % dest)
        finished = []
        rsync = HostRSync(source)
        rsync.add_target_host(gw, finished=lambda: finished.append(1))
        source.join("hello.py").write("world")
        rsync.send()
        gw.exit()
        assert dest.join(source.basename, "hello.py").check()
        assert len(finished) == 1
