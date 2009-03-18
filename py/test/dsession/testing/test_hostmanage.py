
""" RSync filter test
"""

import py
from py.__.test.dsession.hostmanage import HostManager, getconfiggwspecs, getconfigroots
from py.__.execnet.gwmanage import GatewaySpec as Host

from py.__.test import event

def pytest_pyfuncarg_source(pyfuncitem):
    return py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("source")
def pytest_pyfuncarg_dest(pyfuncitem):
    dest = py.test.ensuretemp(pyfuncitem.getmodpath()).mkdir("dest")
    return dest 

class TestHostManager:
    def gethostmanager(self, source, hosts, rsyncdirs=None):
        def opt(optname, l):
            return '%s=%s' % (optname, ",".join(map(str, l)))
        args = [opt('--gateways', hosts)]
        if rsyncdirs:
            args.append(opt('--rsyncdir', [source.join(x, abs=True) for x in rsyncdirs]))
        args.append(source)
        config = py.test.config._reparse(args)
        assert config.topdir == source
        hm = HostManager(config)
        assert hm.gwmanager.specs
        return hm
        
    def xxtest_hostmanager_custom_hosts(self, source, dest):
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session.config, hosts=[1,2,3])
        assert hm.hosts == [1,2,3]

    @py.test.mark.xfail("consider / forbid implicit rsyncdirs?")
    def test_hostmanager_rsync_roots_no_roots(self, source, dest):
        source.ensure("dir1", "file1").write("hello")
        config = py.test.config._reparse([source])
        hm = HostManager(config, hosts=["popen:%s" % dest])
        assert hm.config.topdir == source == config.topdir
        hm.rsync_roots()
        p, = hm.gwmanager.multi_exec("import os ; channel.send(os.getcwd())").receive_each()
        p = py.path.local(p)
        print "remote curdir", p
        assert p == dest.join(config.topdir.basename)
        assert p.join("dir1").check()
        assert p.join("dir1", "file1").check()

    def test_hostmanager_rsync_roots_roots(self, source, dest):
        dir2 = source.ensure("dir1", "dir2", dir=1)
        dir2.ensure("hello")
        hm = self.gethostmanager(source, 
            hosts = ["popen:%s" % dest],
            rsyncdirs = ['dir1']
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
            hosts = ["popen:%s" % dest],
            rsyncdirs = [str(source)]
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
            rsyncdirs = ['dir1/dir2']
        """))
        session = py.test.config._reparse([source]).initsession()
        hm = HostManager(session.config, 
                         hosts=["popen:" + str(dest)])
        hm.rsync_roots()
        assert dest.join("dir2").check()
        assert not dest.join("dir1").check()
        assert not dest.join("bogus").check()

    def test_hostmanager_rsyncignore(self, source, dest):
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
                         hosts=["popen:" + str(dest)])
        hm.rsync_roots()
        assert dest.join("dir1").check()
        assert not dest.join("dir1", "dir2").check()
        assert dest.join("dir5","file").check()
        assert not dest.join("dir6").check()

    def test_hostmanage_optimise_popen(self, source, dest):
        hosts = ["popen"] * 3
        source.join("conftest.py").write("rsyncdirs = ['a']")
        source.ensure('a', dir=1)
        config = py.test.config._reparse([source])
        hm = HostManager(config, hosts=hosts)
        hm.rsync_roots()
        for gwspec in hm.gwmanager.specs:
            assert gwspec.inplacelocal()
            assert not gwspec.joinpath 

    def test_hostmanage_setup_hosts_DEBUG(self, source, EventRecorder):
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

    def test_hostmanage_ssh_setup_hosts(self, testdir):
        sshhost = py.test.config.getvalueorskip("sshhost")
        testdir.makepyfile(__init__="", test_x="""
            def test_one():
                pass
        """)

        sorter = testdir.inline_run("-d", "--rsyncdirs=%s" % testdir.tmpdir, 
                "--gateways=%s" % sshhost, testdir.tmpdir)
        ev = sorter.getfirstnamed("itemtestreport")
        assert ev.passed 

    @py.test.mark.xfail("implement double-rsync test")
    def test_ssh_rsync_samehost_twice(self):
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


def test_getconfiggwspecs_numprocesses():
    config = py.test.config._reparse(['-n3'])
    hosts = getconfiggwspecs(config)
    assert len(hosts) == 3

def test_getconfiggwspecs_disthosts():
    config = py.test.config._reparse(['--gateways=a,b,c'])
    hosts = getconfiggwspecs(config)
    assert len(hosts) == 3
    assert hosts == ['a', 'b', 'c']

def test_getconfigroots(testdir):
    config = testdir.parseconfig('--rsyncdirs=' + str(testdir.tmpdir))
    roots = getconfigroots(config)
    assert len(roots) == 1 + 1 
    assert testdir.tmpdir in roots

def test_getconfigroots_with_conftest(testdir):
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

