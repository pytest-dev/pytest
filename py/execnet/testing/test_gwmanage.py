""" 
    tests for 
    - host specifications
    - managing hosts 
    - manage rsyncing of hosts 

"""

import py
from py.__.execnet.gwmanage import GatewaySpec, GatewayManager
from py.__.execnet.gwmanage import HostRSync

class TestGatewaySpec:
    """
    socket:hostname:port:path SocketGateway
    popen[-executable][:path] PopenGateway
    [ssh:]spec:path           SshGateway
    * [SshGateway]
    """
    def test_popen_nopath(self):
        for joinpath in ('', ':abc', ':ab:cd', ':/x/y'):
            spec = GatewaySpec("popen" + joinpath)
            assert spec.address == "popen"
            assert spec.joinpath == joinpath[1:]
            assert spec.type == "popen"
            spec2 = GatewaySpec("popen" + joinpath)
            self._equality(spec, spec2)
            if joinpath == "":
                assert spec.inplacelocal()
            else:
                assert not spec.inplacelocal()

    def test_ssh(self):
        for prefix in ('ssh:', ''): # ssh is default
            for hostpart in ('x.y', 'xyz@x.y'):
                for joinpath in ('', ':abc', ':ab:cd', ':/tmp'):
                    specstring = prefix + hostpart + joinpath
                    spec = GatewaySpec(specstring)
                    assert spec.address == hostpart 
                    if joinpath[1:]:
                        assert spec.joinpath == joinpath[1:]
                    else:
                        assert spec.joinpath == "pyexecnetcache"
                    assert spec.type == "ssh"
                    spec2 = GatewaySpec(specstring)
                    self._equality(spec, spec2) 
                    assert not spec.inplacelocal()
    
    def test_socket(self):
        for hostpart in ('x.y', 'x', 'popen'):
            for port in ":80", ":1000":
                for joinpath in ('', ':abc', ':abc:de'):
                    spec = GatewaySpec("socket:" + hostpart + port + joinpath)
                    assert spec.address == (hostpart, int(port[1:]))
                    if joinpath[1:]:
                        assert spec.joinpath == joinpath[1:]
                    else:
                        assert spec.joinpath == "pyexecnetcache"
                    assert spec.type == "socket"
                    spec2 = GatewaySpec("socket:" + hostpart + port + joinpath)
                    self._equality(spec, spec2) 
                    assert not spec.inplacelocal()

    def _equality(self, spec1, spec2):
        assert spec1 != spec2
        assert hash(spec1) != hash(spec2)
        assert not (spec1 == spec2)


class TestGatewaySpecAPI:
    def test_popen_nopath_makegateway(self, testdir):
        spec = GatewaySpec("popen")
        gw = spec.makegateway()
        p = gw.remote_exec("import os; channel.send(os.getcwd())").receive()
        curdir = py.std.os.getcwd()
        assert curdir == p
        gw.exit()

    def test_popen_makegateway(self, testdir):
        spec = GatewaySpec("popen:" + str(testdir.tmpdir))
        gw = spec.makegateway()
        p = gw.remote_exec("import os; channel.send(os.getcwd())").receive()
        assert spec.joinpath == p
        gw.exit()

    def test_popen_makegateway_python(self, testdir):
        spec = GatewaySpec("popen")
        gw = spec.makegateway(python=py.std.sys.executable)
        res = gw.remote_exec("import sys ; channel.send(sys.executable)").receive()
        assert py.std.sys.executable == res
        gw.exit()

    def test_ssh(self):
        sshhost = py.test.config.getvalueorskip("sshhost")
        spec = GatewaySpec("ssh:" + sshhost)
        gw = spec.makegateway()
        p = gw.remote_exec("import os ; channel.send(os.getcwd())").receive()
        gw.exit()

    @py.test.mark.xfail("implement socketserver test scenario")
    def test_socketgateway(self):
        gw = py.execnet.PopenGateway()
        spec = GatewaySpec("ssh:" + sshhost)

class TestGatewayManagerPopen:
    def test_hostmanager_popen_makegateway(self):
        hm = GatewayManager(["popen"] * 2)
        hm.makegateways()
        assert len(hm.spec2gateway) == 2
        hm.exit()
        assert not len(hm.spec2gateway) 

    def test_hostmanager_popens_rsync(self, source):
        hm = GatewayManager(["popen"] * 2)
        hm.makegateways()
        assert len(hm.spec2gateway) == 2
        for gw in hm.spec2gateway.values():
            gw.remote_exec = None
        l = []
        hm.rsync(source, notify=lambda *args: l.append(args))
        assert not l
        hm.exit()
        assert not len(hm.spec2gateway) 

    def test_hostmanager_rsync_popen_with_path(self, source, dest):
        hm = GatewayManager(["popen:%s" %dest] * 1)
        hm.makegateways()
        source.ensure("dir1", "dir2", "hello")
        l = []
        hm.rsync(source, notify=lambda *args: l.append(args))
        assert len(l) == 1
        assert l[0] == ("rsyncrootready", hm.spec2gateway.keys()[0], source)
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
        hm = GatewayManager(["popen:hello"] * 2)
        testdir.tmpdir.chdir()
        hellopath = testdir.tmpdir.mkdir("hello")
        hm.makegateways()
        l = [x[1] for x in hm.multi_exec(
                      "import os ; channel.send(os.getcwd())"
                  ).receive_items()
            ]
        paths = [x[1] for x in l]
        assert l == [str(hellopath)] * 2
        py.test.raises(Exception, 'hm.multi_chdir("world", inplacelocal=False)')
        worldpath = hellopath.mkdir("world")
        hm.multi_chdir("world", inplacelocal=False)
        l = hm.multi_exec("import os ; channel.send(os.getcwd())").receive()
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
        l = hm.multi_exec("import os ; channel.send(os.getcwd())").receive()
        assert len(l) == 2
        assert l == [os.getcwd()] * 2

        hm.multi_chdir("hello")
        l = hm.multi_exec("import os ; channel.send(os.getcwd())").receive()
        assert len(l) == 2
        assert l[0] == l[1]
        curwd = os.getcwd()
        assert l[0].startswith(curwd)
        assert l[0].endswith("hello")

from py.__.execnet.gwmanage import MultiChannel
class TestMultiChannel:
    def test_multichannel_receive_items(self):
        class pseudochannel:
            def receive(self):
                return 12

        pc1 = pseudochannel()
        pc2 = pseudochannel()
        multichannel = MultiChannel([pc1, pc2])
        l = multichannel.receive_items()
        assert len(l) == 2
        assert l == [(pc1, 12), (pc2, 12)]

    def test_multichannel_waitclose(self):
        l = []
        class pseudochannel:
            def waitclose(self):
                l.append(0)
        multichannel = MultiChannel([pseudochannel(), pseudochannel()])
        multichannel.waitclose()
        assert len(l) == 2


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
        spec = GatewaySpec("popen:%s" % dest)
        gw = spec.makegateway()
        finished = []
        rsync = HostRSync(source)
        rsync.add_target_host(gw, finished=lambda: finished.append(1))
        source.join("hello.py").write("world")
        rsync.send()
        gw.exit()
        assert dest.join(source.basename, "hello.py").check()
        assert len(finished) == 1

