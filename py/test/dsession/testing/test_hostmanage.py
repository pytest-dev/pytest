
""" RSync filter test
"""

import py
from py.__.test.dsession.hostmanage import HostManager, getconfighosts
from py.__.execnet.gwmanage import GatewaySpec as Host

from py.__.test import event

def pytest_pyfuncarg_source(pyfuncitem):
    return py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("source")
def pytest_pyfuncarg_dest(pyfuncitem):
    dest = py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("dest")
    return dest 

class TestHostManager:
    def gethostmanager(self, source, dist_hosts, dist_rsync_roots=None):
        l = ["dist_hosts = %r" % dist_hosts]
        if dist_rsync_roots:
            l.append("dist_rsync_roots = %r" % dist_rsync_roots)
        source.join("conftest.py").write("\n".join(l))
        config = py.test.config._reparse([source])
        assert config.topdir == source
        hm = HostManager(config)
        assert hm.gwmanager.spec2gateway
        return hm
        
    def xxtest_hostmanager_custom_hosts(self, source, dest):
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session.config, hosts=[1,2,3])
        assert hm.hosts == [1,2,3]

    def test_hostmanager_rsync_roots_no_roots(self, source, dest):
        source.ensure("dir1", "file1").write("hello")
        config = py.test.config._reparse([source])
        hm = HostManager(config, hosts=["localhost:%s" % dest])
        assert hm.config.topdir == source == config.topdir
        hm.rsync_roots()
        p, = hm.gwmanager.multi_exec("import os ; channel.send(os.getcwd())").receive()
        p = py.path.local(p)
        print "remote curdir", p
        assert p == dest.join(config.topdir.basename)
        assert p.join("dir1").check()
        assert p.join("dir1", "file1").check()

    def test_hostmanager_rsync_roots_roots(self, source, dest):
        dir2 = source.ensure("dir1", "dir2", dir=1)
        dir2.ensure("hello")
        hm = self.gethostmanager(source, 
            dist_hosts = ["localhost:%s" % dest],
            dist_rsync_roots = ['dir1']
        )
        assert hm.config.topdir == source
        hm.rsync_roots() 
        assert dest.join("dir1").check()
        assert dest.join("dir1", "dir2").check()
        assert dest.join("dir1", "dir2", 'hello').check()

    def test_hostmanager_init_rsync_topdir_explicit(self, source, dest):
        dir2 = source.ensure("dir1", "dir2", dir=1)
        dir2.ensure("hello")
        hm = self.gethostmanager(source, 
            dist_hosts = ["localhost:%s" % dest],
            dist_rsync_roots = [str(source)]
        )
        assert hm.config.topdir == source
        hm.rsync_roots()
        dest = dest.join(source.basename)
        assert dest.join("dir1").check()
        assert dest.join("dir1", "dir2").check()
        assert dest.join("dir1", "dir2", 'hello').check()

    def test_hostmanager_init_rsync_roots(self, source, dest):
        dir2 = source.ensure("dir1", "dir2", dir=1)
        source.ensure("dir1", "somefile", dir=1)
        dir2.ensure("hello")
        source.ensure("bogusdir", "file")
        source.join("conftest.py").write(py.code.Source("""
            dist_rsync_roots = ['dir1/dir2']
        """))
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session.config, 
                         hosts=["localhost:" + str(dest)])
        hm.rsync_roots()
        assert dest.join("dir2").check()
        assert not dest.join("dir1").check()
        assert not dest.join("bogus").check()

    def test_hostmanager_rsync_ignore(self, source, dest):
        dir2 = source.ensure("dir1", "dir2", dir=1)
        dir5 = source.ensure("dir5", "dir6", "bogus")
        dirf = source.ensure("dir5", "file")
        dir2.ensure("hello")
        source.join("conftest.py").write(py.code.Source("""
            dist_rsync_ignore = ['dir1/dir2', 'dir5/dir6']
            dist_rsync_roots = ['dir1', 'dir5']
        """))
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session.config,
                         hosts=["localhost:" + str(dest)])
        hm.rsync_roots()
        assert dest.join("dir1").check()
        assert not dest.join("dir1", "dir2").check()
        assert dest.join("dir5","file").check()
        assert not dest.join("dir6").check()

    def test_hostmanage_optimise_localhost(self, source, dest):
        hosts = ["localhost"] * 3
        source.join("conftest.py").write("dist_rsync_roots = ['a']")
        source.ensure('a', dir=1)
        config = py.test.config._reparse([source])
        hm = HostManager(config, hosts=hosts)
        hm.rsync_roots()
        for gwspec in hm.gwmanager.spec2gateway:
            assert gwspec.inplacelocal()
            assert not gwspec.joinpath 

    def test_hostmanage_setup_hosts(self, source):
        hosts = ["localhost"] * 3
        source.join("conftest.py").write("dist_rsync_roots = ['a']")
        source.ensure('a', dir=1)
        config = py.test.config._reparse([source])
        hm = HostManager(config, hosts=hosts)
        queue = py.std.Queue.Queue()
        hm.setup_hosts(putevent=queue.put)
        for host in hm.gwmanager.spec2gateway:
            eventcall = queue.get(timeout=2.0)
            name, args, kwargs = eventcall
            assert name == "hostup"
        for host in hm.gwmanager.spec2gateway:
            host.node.shutdown()
        for host in hm.gwmanager.spec2gateway:
            eventcall = queue.get(timeout=2.0)
            name, args, kwargs = eventcall
            print name, args, kwargs
            assert name == "hostdown"

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


def test_getconfighosts():
    config = py.test.config._reparse(['-n3'])
    hosts = getconfighosts(config)
    assert len(hosts) == 3

