
""" RSync filter test
"""

import py
from py.__.test.rsession.hostmanage import HostRSync 
from py.__.test.rsession.hostmanage import HostInfo, HostManager 

class DirSetup:
    def setup_method(self, method):
        name = "%s.%s" %(self.__class__.__name__, method.func_name)
        self.tmpdir = py.test.ensuretemp(name)
        self.source = self.tmpdir.ensure("source", dir=1)
        self.dest = self.tmpdir.join("dest")

class TestHostInfo:
    def test_defaultpath(self):
        x = HostInfo("localhost")
        assert x.hostname == "localhost"
        assert x.relpath == "pytestcache-" + x.hostname 

    def test_path(self):
        x = HostInfo("localhost:/tmp")
        assert x.relpath == "/tmp"
        assert x.hostname == "localhost"

    def test_hostid(self):
        x = HostInfo("localhost")
        y = HostInfo("localhost")
        assert x.hostid != y.hostid 
        x = HostInfo("localhost:/tmp")
        y = HostInfo("localhost")
        assert x.hostid != y.hostid 

    def test_non_existing_hosts(self):
        host = HostInfo("alskdjalsdkjasldkajlsd")
        py.test.raises((py.process.cmdexec.Error, IOError, EOFError), 
                       host.initgateway)

    def test_initgateway_localhost_relpath(self):
        name = "pytestcache-localhost"
        x = HostInfo("localhost:%s" % name)
        x.initgateway()
        assert x.gw
        try:
            homedir = py.path.local(py.std.os.environ['HOME'])
            expected = homedir.join(name) 
            assert x.gw_remotepath == str(expected)
            assert x.localdest == expected 
        finally:
            x.gw.exit()


    def test_initgateway_ssh_and_remotepath(self):
        option = py.test.config.option
        if option.sshtarget is None: 
            py.test.skip("no known ssh target, use -S to set one")
        x = HostInfo("%s" % (option.sshtarget, ))
        x.initgateway()
        assert x.gw
        assert x.gw_remotepath.endswith(x.relpath)
        channel = x.gw.remote_exec("""
            import os
            homedir = os.environ['HOME']
            relpath = channel.receive()
            path = os.path.join(homedir, relpath)
            channel.send(path) 
        """)
        channel.send(x.relpath)
        res = channel.receive()
        assert res == x.gw_remotepath
        assert x.localdest is None

class TestSyncing(DirSetup): 
    def test_hrsync_filter(self):
        self.source.ensure("dir", "file.txt")
        self.source.ensure(".svn", "entries")
        self.source.ensure(".somedotfile", "moreentries")
        self.source.ensure("somedir", "editfile~")
        syncer = HostRSync()
        l = list(self.source.visit(rec=syncer.filter,
                                   fil=syncer.filter))
        assert len(l) == 3
        basenames = [x.basename for x in l]
        assert 'dir' in basenames
        assert 'file.txt' in basenames
        assert 'somedir' in basenames

    def test_hrsync_one_host(self):
        h1 = HostInfo("localhost:%s" % self.dest)
        finished = []
        rsync = HostRSync()
        h1.initgateway()
        rsync.add_target_host(h1)
        self.source.join("hello.py").write("world")
        rsync.send(self.source)
        assert self.dest.join("hello.py").check()

    def test_hrsync_same_host_twice(self):
        h1 = HostInfo("localhost:%s" % self.dest)
        h2 = HostInfo("localhost:%s" % self.dest)
        finished = []
        rsync = HostRSync()
        l = []
        h1.initgateway()
        res1 = rsync.add_target_host(h1)
        assert res1
        res2 = rsync.add_target_host(h2)
        assert not res2

class TestHostManager(DirSetup):
    def test_hostmanager_custom_hosts(self):
        config = py.test.config._reparse([self.source])
        hm = HostManager(config, hosts=[1,2,3])
        assert hm.hosts == [1,2,3]

    def test_hostmanager_init_rsync_topdir(self):
        dir2 = self.source.ensure("dir1", "dir2", dir=1)
        dir2.ensure("hello")
        config = py.test.config._reparse([self.source])
        hm = HostManager(config, 
                hosts=[HostInfo("localhost:" + str(self.dest))])
        events = []
        hm.init_rsync(reporter=events.append)
        assert self.dest.join("dir1").check()
        assert self.dest.join("dir1", "dir2").check()
        assert self.dest.join("dir1", "dir2", 'hello').check()

    def test_hostmanager_init_rsync_rsync_roots(self):
        dir2 = self.source.ensure("dir1", "dir2", dir=1)
        dir2.ensure("hello")
        self.source.ensure("bogusdir", "file")
        self.source.join("conftest.py").write(py.code.Source("""
            dist_rsync_roots = ['dir1/dir2']
        """))
        config = py.test.config._reparse([self.source])
        hm = HostManager(config, 
                         hosts=[HostInfo("localhost:" + str(self.dest))])
        events = []
        hm.init_rsync(reporter=events.append)
        assert self.dest.join("dir1").check()
        assert self.dest.join("dir1", "dir2").check()
        assert self.dest.join("dir1", "dir2", 'hello').check()
        assert not self.dest.join("bogus").check()
