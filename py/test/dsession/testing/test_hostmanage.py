
""" RSync filter test
"""

import py
from py.__.test.dsession.hostmanage import HostRSync, Host, HostManager, gethosts
from py.__.test.dsession.hostmanage import sethomedir, gethomedir, getpath_relto_home
from py.__.test import event

class TestHost:
    def _gethostinfo(self, testdir, relpath=""):
        exampledir = testdir.mkdir("gethostinfo")
        if relpath:
            exampledir = exampledir.join(relpath)
        hostinfo = Host("localhost:%s" % exampledir)
        return hostinfo

    def test_defaultpath(self):
        x = Host("localhost:")
        assert x.hostname == "localhost"
        assert not x.relpath

    def test_addrel(self):
        host = Host("localhost:", addrel="whatever")
        assert host.inplacelocal 
        assert not host.relpath 
        host = Host("localhost:/tmp", addrel="base")
        assert host.relpath == "/tmp/base"
        host = Host("localhost:tmp", addrel="base2")
        assert host.relpath == "tmp/base2"

    def test_path(self):
        x = Host("localhost:/tmp")
        assert x.relpath == "/tmp"
        assert x.hostname == "localhost"
        assert not x.inplacelocal 

    def test_equality(self):
        x = Host("localhost:")
        y = Host("localhost:")
        assert x != y
        assert not (x == y)

    def test_hostid(self):
        x = Host("localhost:")
        y = Host("localhost:")
        assert x.hostid != y.hostid 
        x = Host("localhost:/tmp")
        y = Host("localhost:")
        assert x.hostid != y.hostid 

    def test_non_existing_hosts(self):
        host = Host("alskdjalsdkjasldkajlsd")
        py.test.raises((py.process.cmdexec.Error, IOError, EOFError), 
                       host.initgateway)

    def test_remote_has_homedir_as_currentdir(self, testdir):
        host = self._gethostinfo(testdir)
        old = py.path.local.get_temproot().chdir()
        try:
            host.initgateway()
            channel = host.gw.remote_exec(py.code.Source(
                gethomedir, """
                import os
                homedir = gethomedir()
                curdir = os.getcwd()
                channel.send((curdir, homedir))
            """))
            remote_curdir, remote_homedir = channel.receive()
            assert remote_curdir == remote_homedir 
        finally:
            old.chdir()

    def test_initgateway_localhost_relpath(self):
        host = Host("localhost:somedir")
        host.initgateway()
        assert host.gw
        try:
            homedir = py.path.local._gethomedir() 
            expected = homedir.join("somedir")
            assert host.gw_remotepath == str(expected)
        finally:
            host.gw.exit()

    def test_initgateway_python(self):
        host = Host("localhost", python="python2.4")
        l = []
        def p(python):
            l.append(python)
            raise ValueError
        py.magic.patch(py.execnet, 'PopenGateway', p)
        try:
            py.test.raises(ValueError, host.initgateway)
        finally:
            py.magic.revert(py.execnet, 'PopenGateway')
        assert l[0] == host.python

    def test_initgateway_ssh_and_remotepath(self):
        hostspec = py.test.config.option.sshhost
        if not hostspec:
            py.test.skip("no known ssh target, use -S to set one")
        host = Host("%s" % (hostspec))
        # this test should be careful to not write/rsync anything
        # as the remotepath is the default location 
        # and may be used in the real world 
        host.initgateway()
        assert host.gw
        assert host.gw_remotepath.endswith(host.relpath)
        channel = host.gw.remote_exec("""
            import os
            homedir = os.environ['HOME']
            relpath = channel.receive()
            path = os.path.join(homedir, relpath)
            channel.send(path) 
        """)
        channel.send(host.relpath)
        res = channel.receive()
        assert res == host.gw_remotepath

def pytest_pyfuncarg_source(pyfuncitem):
    return py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("source")
def pytest_pyfuncarg_dest(pyfuncitem):
    return py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("dest")

class TestSyncing:
    def _gethostinfo(self, dest):
        hostinfo = Host("localhost:%s" % dest)
        return hostinfo 
        
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

    def test_hrsync_localhost_inplace(self, source, dest):
        h1 = Host("localhost")
        events = []
        rsync = HostRSync(source)
        h1.initgateway()
        rsync.add_target_host(h1, notify=events.append)
        assert events
        l = [x for x in events 
                if isinstance(x, event.HostRSyncing)]
        assert len(l) == 1
        ev = l[0]
        assert ev.host == h1
        assert ev.root == ev.remotepath 
        l = [x for x in events 
                if isinstance(x, event.HostRSyncRootReady)]
        assert len(l) == 1
        ev = l[0]
        assert ev.root == source
        assert ev.host == h1

    def test_hrsync_one_host(self, source, dest):
        h1 = self._gethostinfo(dest)
        finished = []
        rsync = HostRSync(source)
        h1.initgateway()
        rsync.add_target_host(h1)
        source.join("hello.py").write("world")
        rsync.send()
        assert dest.join("hello.py").check()

    def test_hrsync_same_host_twice(self, source, dest):
        h1 = self._gethostinfo(dest)
        h2 = self._gethostinfo(dest)
        finished = []
        rsync = HostRSync(source)
        l = []
        h1.initgateway()
        h2.initgateway()
        res1 = rsync.add_target_host(h1)
        assert res1
        res2 = rsync.add_target_host(h2)
        assert not res2

class TestHostManager:
    def gethostmanager(self, source, dist_hosts, dist_rsync_roots=None):
        l = ["dist_hosts = %r" % dist_hosts]
        if dist_rsync_roots:
            l.append("dist_rsync_roots = %r" % dist_rsync_roots)
        source.join("conftest.py").write("\n".join(l))
        config = py.test.config._reparse([source])
        assert config.topdir == source
        session = config.initsession()
        hm = HostManager(session)
        assert hm.hosts
        return hm
        
    def test_hostmanager_custom_hosts(self, source, dest):
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session, hosts=[1,2,3])
        assert hm.hosts == [1,2,3]

    def test_hostmanager_init_rsync_topdir(self, source, dest):
        dir2 = source.ensure("dir1", "dir2", dir=1)
        dir2.ensure("hello")
        hm = self.gethostmanager(source, 
            dist_hosts = ["localhost:%s" % dest]
        )
        assert hm.session.config.topdir == source
        hm.init_rsync() 
        dest = dest.join(source.basename)
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
        assert hm.session.config.topdir == source
        hm.init_rsync()
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
        hm = HostManager(session, 
                         hosts=[Host("localhost:" + str(dest))])
        hm.init_rsync()
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
        """))
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session,
                         hosts=[Host("localhost:" + str(dest))])
        hm.init_rsync()
        assert dest.join("dir1").check()
        assert not dest.join("dir1", "dir2").check()
        assert dest.join("dir5","file").check()
        assert not dest.join("dir6").check()

    def test_hostmanage_optimise_localhost(self, source, dest):
        hosts = [Host("localhost") for i in range(3)]
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session, hosts=hosts)
        hm.init_rsync()
        for host in hosts:
            assert host.inplacelocal
            assert host.gw_remotepath is None
            assert not host.relpath 

    def test_hostmanage_setup_hosts(self, source):
        hosts = [Host("localhost") for i in range(3)]
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session, hosts=hosts)
        queue = py.std.Queue.Queue()
        hm.setup_hosts(putevent=queue.put)
        for host in hm.hosts:
            eventcall = queue.get(timeout=2.0)
            name, args, kwargs = eventcall
            assert name == "hostup"
        for host in hm.hosts:
            host.node.shutdown()
        for host in hm.hosts:
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


def test_getpath_relto_home():
    x = getpath_relto_home("hello")
    assert x == py.path.local._gethomedir().join("hello")
    x = getpath_relto_home(".")
    assert x == py.path.local._gethomedir()

def test_sethomedir():
    old = py.path.local.get_temproot().chdir()
    try:
        sethomedir()
        curdir = py.path.local()
    finally:
        old.chdir()

    assert py.path.local._gethomedir() == curdir

def test_gethosts():
    config = py.test.config._reparse(['-n3'])
    hosts = gethosts(config, '')
    assert len(hosts) == 3

