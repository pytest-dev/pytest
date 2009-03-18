""" 
    tests for 
    - gateway specifications
    - multi channels and multi gateways 
    - gateway management 
    - manage rsyncing of hosts 

"""

import py
from py.__.execnet.gwmanage import GatewayManager, HostRSync

class TestGatewayManagerPopen:
    def test_hostmanager_popen_makegateway(self):
        hm = GatewayManager(["popen"] * 2)
        hm.makegateways()
        assert len(hm.gateways) == 2
        hm.exit()
        assert not len(hm.gateways) 

    def test_hostmanager_popens_rsync(self, source):
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

    def test_hostmanager_rsync_popen_with_path(self, source, dest):
        hm = GatewayManager(["popen::%s" %dest] * 1)
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

    def XXXtest_ssh_rsync_samehost_twice(self):
        #XXX we have no easy way to have a temp directory remotely!
        option = py.test.config.option
        if option.sshhost is None: 
            py.test.skip("no known ssh target, use -S to set one")
        host1 = Host("%s" % (option.sshhost, ))
        host2 = Host("%s" % (option.sshhost, ))
        hm = HostManager(config, hosts=[host1, host2])
        events = []
        hm.init_rsync(events.append)
        print events
        assert 0

    def test_multi_chdir_popen_with_path(self, testdir):
        import os
        hm = GatewayManager(["popen::hello"] * 2)
        testdir.tmpdir.chdir()
        hellopath = testdir.tmpdir.mkdir("hello")
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
        assert l == [os.getcwd()] * 2

        hm.multi_chdir("hello")
        l = hm.multi_exec("import os ; channel.send(os.getcwd())").receive_each()
        assert len(l) == 2
        assert l[0] == l[1]
        curwd = os.getcwd()
        assert l[0].startswith(curwd)
        assert l[0].endswith("hello")

def pytest_pyfuncarg_source(pyfuncitem):
    return py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("source")
def pytest_pyfuncarg_dest(pyfuncitem):
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
        spec = py.execnet.GatewaySpec("popen::%s" % dest)
        gw = spec.makegateway()
        finished = []
        rsync = HostRSync(source)
        rsync.add_target_host(gw, finished=lambda: finished.append(1))
        source.join("hello.py").write("world")
        rsync.send()
        gw.exit()
        assert dest.join(source.basename, "hello.py").check()
        assert len(finished) == 1

