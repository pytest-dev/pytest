
""" RSync filter test
"""

import py
from py.__.test.dsession.hostmanage import HostManager, getxspecs, getconfigroots

from py.__.test import event

def pytest_pyfuncarg_source(pyfuncitem):
    return py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("source")
def pytest_pyfuncarg_dest(pyfuncitem):
    dest = py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("dest")
    return dest 

class TestHostManager:
    @py.test.mark.xfail("consider / forbid implicit rsyncdirs?")
    def test_hostmanager_rsync_roots_no_roots(self, source, dest):
        source.ensure("dir1", "file1").write("hello")
        config = py.test.config._reparse([source])
        hm = HostManager(config, hosts=["popen::%s" % dest])
        assert hm.config.topdir == source == config.topdir
        hm.rsync_roots()
        p, = hm.gwmanager.multi_exec("import os ; channel.send(os.getcwd())").receive_each()
        p = py.path.local(p)
        print "remote curdir", p
        assert p == dest.join(config.topdir.basename)
        assert p.join("dir1").check()
        assert p.join("dir1", "file1").check()

    def test_popen_rsync_subdir(self, testdir, source, dest):
        dir1 = source.mkdir("dir1")
        dir2 = dir1.mkdir("dir2")
        dir2.ensure("hello")
        for rsyncroot in (dir1, source):
            dest.remove()
            hm = HostManager(testdir.parseconfig(
                "--tx", "popen//chdir=%s" % dest,
                "--rsyncdirs", rsyncroot,
                source, 
            ))
            assert hm.config.topdir == source
            hm.rsync_roots() 
            if rsyncroot == source:
                dest = dest.join("source")
            assert dest.join("dir1").check()
            assert dest.join("dir1", "dir2").check()
            assert dest.join("dir1", "dir2", 'hello').check()

    def test_init_rsync_roots(self, source, dest):
        dir2 = source.ensure("dir1", "dir2", dir=1)
        source.ensure("dir1", "somefile", dir=1)
        dir2.ensure("hello")
        source.ensure("bogusdir", "file")
        source.join("conftest.py").write(py.code.Source("""
            rsyncdirs = ['dir1/dir2']
        """))
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session.config, 
                         hosts=["popen//chdir=%s" % dest])
        hm.rsync_roots()
        assert dest.join("dir2").check()
        assert not dest.join("dir1").check()
        assert not dest.join("bogus").check()

    def test_rsyncignore(self, source, dest):
        dir2 = source.ensure("dir1", "dir2", dir=1)
        dir5 = source.ensure("dir5", "dir6", "bogus")
        dirf = source.ensure("dir5", "file")
        dir2.ensure("hello")
        source.join("conftest.py").write(py.code.Source("""
            rsyncdirs = ['dir1', 'dir5']
            rsyncignore = ['dir1/dir2', 'dir5/dir6']
        """))
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session.config,
                         hosts=["popen//chdir=%s" % dest])
        hm.rsync_roots()
        assert dest.join("dir1").check()
        assert not dest.join("dir1", "dir2").check()
        assert dest.join("dir5","file").check()
        assert not dest.join("dir6").check()

    def test_optimise_popen(self, source, dest):
        hosts = ["popen"] * 3
        source.join("conftest.py").write("rsyncdirs = ['a']")
        source.ensure('a', dir=1)
        config = py.test.config._reparse([source])
        hm = HostManager(config, hosts=hosts)
        hm.rsync_roots()
        for gwspec in hm.gwmanager.specs:
            assert gwspec._samefilesystem()
            assert not gwspec.chdir

    def test_setup_hosts_DEBUG(self, source, EventRecorder):
        hosts = ["popen"] * 2
        source.join("conftest.py").write("rsyncdirs = ['a']")
        source.ensure('a', dir=1)
        config = py.test.config._reparse([source, '--debug'])
        assert config.option.debug
        hm = HostManager(config, hosts=hosts)
        evrec = EventRecorder(config.bus, debug=True)
        hm.setup_hosts(putevent=[].append)
        for host in hm.gwmanager.specs:
            l = evrec.getnamed("trace")
            print evrec.events
            assert l 
        hm.teardown_hosts()

    def test_ssh_setup_hosts(self, specssh, testdir):
        testdir.makepyfile(__init__="", test_x="""
            def test_one():
                pass
        """)
        sorter = testdir.inline_run("-d", "--rsyncdirs=%s" % testdir.tmpdir, 
                "--tx=%s" % specssh, testdir.tmpdir)
        ev = sorter.getfirstnamed("itemtestreport")
        assert ev.passed 

class TestOptionsAndConfiguration:
    def test_getxspecs_numprocesses(self, testdir):
        config = testdir.parseconfig("-n3")
        xspecs = getxspecs(config)
        assert len(xspecs) == 3

    def test_getxspecs(self, testdir):
        config = testdir.parseconfig("--tx=popen", "--tx", "ssh=xyz")
        xspecs = getxspecs(config)
        assert len(xspecs) == 2
        print xspecs
        assert xspecs[0].popen 
        assert xspecs[1].ssh == "xyz"

    def test_getconfigroots(self, testdir):
        config = testdir.parseconfig('--rsyncdirs=' + str(testdir.tmpdir))
        roots = getconfigroots(config)
        assert len(roots) == 1 + 1 
        assert testdir.tmpdir in roots

    def test_getconfigroots_with_conftest(self, testdir):
        testdir.chdir()
        p = py.path.local()
        for bn in 'x y z'.split():
            p.mkdir(bn)
        testdir.makeconftest("""
            rsyncdirs= 'x', 
        """)
        config = testdir.parseconfig(testdir.tmpdir, '--rsyncdirs=y,z')
        roots = getconfigroots(config)
        assert len(roots) == 3 + 1 
        assert py.path.local('y') in roots 
        assert py.path.local('z') in roots 
        assert testdir.tmpdir.join('x') in roots 

