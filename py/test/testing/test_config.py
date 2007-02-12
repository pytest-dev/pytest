from __future__ import generators
import py

from py.__.test.config import gettopdir
from py.__.test.testing.test_collect import skipboxed

def test_tmpdir():
    d1 = py.test.ensuretemp('hello') 
    d2 = py.test.ensuretemp('hello') 
    assert d1 == d2
    assert d1.check(dir=1) 

def test_config_cmdline_options(): 
    o = py.test.ensuretemp('configoptions') 
    o.ensure("conftest.py").write(py.code.Source(""" 
        import py
        def _callback(option, opt_str, value, parser, *args, **kwargs):
            option.tdest = True
        Option = py.test.config.Option
        option = py.test.config.addoptions("testing group", 
            Option('-G', '--glong', action="store", default=42,
                   type="int", dest="gdest", help="g value."), 
            # XXX note: special case, option without a destination
            Option('-T', '--tlong', action="callback", callback=_callback,
                    help='t value'),
            )
        """))
    old = o.chdir() 
    try: 
        config = py.test.config._reparse(['-G', '17'])
    finally: 
        old.chdir() 
    assert config.option.gdest == 17 

def test_config_cmdline_options_only_lowercase(): 
    o = py.test.ensuretemp('test_config_cmdline_options_only_lowercase')
    o.ensure("conftest.py").write(py.code.Source(""" 
        import py
        Option = py.test.config.Option
        options = py.test.config.addoptions("testing group", 
            Option('-g', '--glong', action="store", default=42,
                   type="int", dest="gdest", help="g value."), 
            )
        """))
    old = o.chdir() 
    try: 
        py.test.raises(ValueError, """
            py.test.config._reparse(['-g', '17'])
        """)
    finally: 
        old.chdir() 

def test_parsing_again_fails():
    dir = py.test.ensuretemp("parsing_again_fails")
    config = py.test.config._reparse([str(dir)])
    py.test.raises(AssertionError, "config.parse([])")

def test_config_getvalue_honours_conftest():
    o = py.test.ensuretemp('testconfigget') 
    o.ensure("conftest.py").write("x=1")
    o.ensure("sub", "conftest.py").write("x=2 ; y = 3")
    config = py.test.config._reparse([str(o)])
    assert config.getvalue("x") == 1
    assert config.getvalue("x", o.join('sub')) == 2
    py.test.raises(KeyError, "config.getvalue('y')")
    config = py.test.config._reparse([str(o.join('sub'))])
    assert config.getvalue("x") == 2
    assert config.getvalue("y") == 3
    assert config.getvalue("x", o) == 1
    py.test.raises(KeyError, 'config.getvalue("y", o)')


def test_siblingconftest_fails_maybe():
    from py.__.test import config
    cfg = config.Config()
    o = py.test.ensuretemp('siblingconftest')
    o.ensure("__init__.py")
    o.ensure("sister1", "__init__.py")
    o.ensure("sister1", "conftest.py").write(py.code.Source("""
        x = 2
    """))
        
    o.ensure("sister2", "__init__.py")
    o.ensure("sister2", "conftest.py").write(py.code.Source("""
        raise SyntaxError
    """))

    assert cfg.getvalue(path=o.join('sister1'), name='x') == 2
    old = o.chdir()
    try:
        pytestpath = py.magic.autopath().dirpath().dirpath().dirpath().join(
                        'bin/py.test')
        print py.process.cmdexec('python "%s" sister1' % (pytestpath,))
        o.join('sister1').chdir()
        print py.process.cmdexec('python "%s"' % (pytestpath,))
    finally:
        old.chdir()

def test_config_overwrite():
    o = py.test.ensuretemp('testconfigget') 
    o.ensure("conftest.py").write("x=1")
    config = py.test.config._reparse([str(o)])
    assert config.getvalue('x') == 1
    config.option.x = 2
    assert config.getvalue('x') == 2
    config = py.test.config._reparse([str(o)])
    assert config.getvalue('x') == 1

def test_gettopdir():
    tmp = py.test.ensuretemp("topdir")
    assert gettopdir([tmp]) == tmp
    topdir =gettopdir([tmp.join("hello"), tmp.join("world")])
    assert topdir == tmp 

def test_gettopdir_pypkg():
    tmp = py.test.ensuretemp("topdir2")
    a = tmp.ensure('a', dir=1)
    b = tmp.ensure('a', 'b', '__init__.py')
    c = tmp.ensure('a', 'b', 'c.py')
    Z = tmp.ensure('Z', dir=1)
    assert gettopdir([c]) == a
    assert gettopdir([c, Z]) == tmp 


def test_config_init_direct():
    tmp = py.test.ensuretemp("_initdirect")
    tmp.ensure("__init__.py")
    tmp.ensure("conftest.py").write("x=1 ; y=2")
    hello = tmp.ensure("test_hello.py")
    config = py.test.config._reparse([hello])
    repr = config._makerepr(conftestnames=['x', 'y'])
    config2 = py.test.config._reparse([tmp.dirpath()])
    config2._initialized = False # we have to do that from tests
    config2._initdirect(topdir=tmp.dirpath(), repr=repr)
    for col1, col2 in zip(config.getcolitems(), config2.getcolitems()):
        assert col1.fspath == col2.fspath
    py.test.raises(AssertionError, "config2._initdirect(None, None)")
    from py.__.test.config import Config
    config3 = Config()
    config3._initdirect(topdir=tmp.dirpath(), repr=repr,
        coltrails=[(tmp.basename, (hello.basename,))])
    assert config3.getvalue('x') == 1
    assert config3.getvalue('y') == 2
    cols = config.getcolitems()
    assert len(cols) == 1
    col = cols[0]
    assert col.name == 'test_hello.py'
    assert col.parent.name == tmp.basename 
    assert col.parent.parent is None 

def test_config_make_and__mergerepr():
    tmp = py.test.ensuretemp("reprconfig1")
    tmp.ensure("__init__.py")
    tmp.ensure("conftest.py").write("x=1")
    config = py.test.config._reparse([tmp])
    repr = config._makerepr(conftestnames=['x'])
    config.option.verbose = 42
    repr2 = config._makerepr(conftestnames=[], optnames=['verbose'])
    config = py.test.config._reparse([tmp.dirpath()])
    py.test.raises(KeyError, "config.getvalue('x')")
    config._mergerepr(repr)
    assert config.getvalue('x') == 1
    config._mergerepr(repr2) 
    assert config.option.verbose == 42

def test_config_marshability():
    tmp = py.test.ensuretemp("configmarshal") 
    tmp.ensure("__init__.py")
    tmp.ensure("conftest.py").write("a = object()")
    config = py.test.config._reparse([tmp])
    py.test.raises(ValueError, "config._makerepr(conftestnames=['a'])")

    config.option.hello = lambda x: None
    py.test.raises(ValueError, "config._makerepr(conftestnames=[])")
    config._makerepr(conftestnames=[], optnames=[])

def test_config_rconfig():
    tmp = py.test.ensuretemp("rconfigopt")
    tmp.ensure("__init__.py")
    tmp.ensure("conftest.py").write(py.code.Source("""
    import py
    Option = py.test.config.Option
    option = py.test.config.addoptions("testing group", 
            Option('-G', '--glong', action="store", default=42,
                   type="int", dest="gdest", help="g value."))
    """))
    config = py.test.config._reparse([tmp, "-G", "11"])
    assert config.option.gdest == 11
    repr = config._makerepr(conftestnames=[])
    config = py.test.config._reparse([tmp.dirpath()])
    py.test.raises(AttributeError, "config.option.gdest")
    config._mergerepr(repr) 
    assert config.option.gdest == 11

class TestSessionAndOptions: 
    def setup_class(cls):
        cls.tmproot = py.test.ensuretemp(cls.__name__)

    def setup_method(self, method):
        self.tmpdir = self.tmproot.ensure(method.__name__, dir=1) 

    def test_sessionname_default(self):
        config = py.test.config._reparse([self.tmpdir])
        assert config._getsessionname() == 'TerminalSession'

    def test_sessionname_dist(self):
        config = py.test.config._reparse([self.tmpdir, '--dist'])
        assert config._getsessionname() == 'RSession'

    def test_implied_lsession(self):
        optnames = 'startserver runbrowser apigen=x rest boxed'.split()
        for x in optnames:
            config = py.test.config._reparse([self.tmpdir, '--%s' % x])
            assert config._getsessionname() == 'LSession'

        for x in 'startserver runbrowser rest'.split():
            config = py.test.config._reparse([self.tmpdir, '--dist', '--%s' % x])
            assert config._getsessionname() == 'RSession'

    def test_implied_remote_terminal_session(self):
        config = py.test.config._reparse([self.tmpdir, '--looponfailing'])
        assert config._getsessionname() == 'RemoteTerminalSession'
        config = py.test.config._reparse([self.tmpdir, '--exec=x'])
        assert config._getsessionname() == 'RemoteTerminalSession'
        config = py.test.config._reparse([self.tmpdir, '--dist', '--exec=x'])
        assert config._getsessionname() == 'RSession'

    def test_sessionname_lookup_custom(self):
        self.tmpdir.join("conftest.py").write(py.code.Source("""
            from py.__.test.session import Session
            class MySession(Session):
                def __init__(self, config):
                    self.config = config 
        """)) 
        config = py.test.config._reparse(["--session=MySession", self.tmpdir])
        session = config.initsession()
        assert session.__class__.__name__ == 'MySession'

    def test_initsession(self):
        config = py.test.config._reparse([self.tmpdir])
        session = config.initsession()
        assert session.config is config 

    def test_boxed_option_default(self):
        self.tmpdir.join("conftest.py").write("dist_hosts=[]")
        tmpdir = self.tmpdir.ensure("subdir", dir=1)
        config = py.test.config._reparse([tmpdir])
        config.initsession()
        assert not config.option.boxed
        config = py.test.config._reparse(['--dist', tmpdir])
        config.initsession()
        assert not config.option.boxed

    def test_boxed_option_from_conftest(self):
        self.tmpdir.join("conftest.py").write("dist_hosts=[]")
        tmpdir = self.tmpdir.ensure("subdir", dir=1)
        tmpdir.join("conftest.py").write(py.code.Source("""
            dist_hosts = []
            dist_boxed = True
        """))
        config = py.test.config._reparse(['--dist', tmpdir])
        config.initsession()
        assert config.option.boxed 

    def test_boxed_option_from_conftest2(self):
        tmpdir = self.tmpdir
        tmpdir.join("conftest.py").write(py.code.Source("""
            dist_boxed = False
        """))
        config = py.test.config._reparse([tmpdir, '--box'])
        assert config.option.boxed 
        config.initsession()
        assert config.option.boxed

    def test_dist_session_no_capturedisable(self):
        config = py.test.config._reparse([self.tmpdir, '-d', '-s'])
        py.test.raises(SystemExit, "config.initsession()")

    def test_getvalue_pathlist(self):
        tmpdir = self.tmpdir
        somepath = tmpdir.join("x", "y", "z")
        p = tmpdir.join("conftest.py")
        p.write("pathlist = ['.', %r]" % str(somepath))
        config = py.test.config._reparse([p])
        assert config.getvalue_pathlist('notexist') is None
        pl = config.getvalue_pathlist('pathlist')
        print pl
        assert len(pl) == 2
        assert pl[0] == tmpdir
        assert pl[1] == somepath

        config.option.mypathlist = [py.path.local()]
        pl = config.getvalue_pathlist('mypathlist')
        assert pl == [py.path.local()]

    def test_config_iocapturing(self):
        self.tmpdir
        config = py.test.config._reparse([self.tmpdir])
        assert config.getvalue("conf_iocapture")
        tmpdir = self.tmpdir.ensure("sub-with-conftest", dir=1)
        tmpdir.join("conftest.py").write(py.code.Source("""
            conf_iocapture = "sys"
        """))
        config = py.test.config._reparse([tmpdir])
        assert config.getvalue("conf_iocapture") == "sys"
        class dummy: pass
        config._startcapture(dummy)
        print 42
        py.std.os.write(1, "23")
        config._finishcapture(dummy)
        assert dummy._captured_out.strip() == "42"
        
        config = py.test.config._reparse([tmpdir.dirpath()])
        config._startcapture(dummy, path=tmpdir)
        print 42
        py.std.os.write(1, "23")
        config._finishcapture(dummy)
        assert dummy._captured_out.strip() == "42"

class TestConfigColitems:
    def setup_class(cls):
        cls.tmproot = py.test.ensuretemp(cls.__name__)

    def setup_method(self, method):
        self.tmpdir = self.tmproot.mkdir(method.__name__) 
    
    def test_getcolitems_onedir(self):
        config = py.test.config._reparse([self.tmpdir])
        colitems = config.getcolitems()
        assert len(colitems) == 1
        col = colitems[0]
        assert isinstance(col, py.test.collect.Directory)
        for col in col.listchain():
            assert col._config is config 

    def test_getcolitems_twodirs(self):
        config = py.test.config._reparse([self.tmpdir, self.tmpdir])
        colitems = config.getcolitems()
        assert len(colitems) == 2
        col1, col2 = colitems 
        assert col1.name == col2.name 
        assert col1.parent == col2.parent 

    def test_getcolitems_curdir_and_subdir(self):
        a = self.tmpdir.ensure("a", dir=1)
        config = py.test.config._reparse([self.tmpdir, a])
        colitems = config.getcolitems()
        assert len(colitems) == 2
        col1, col2 = colitems 
        assert col1.name == self.tmpdir.basename
        assert col2.name == 'a'
        for col in colitems:
            for subcol in col.listchain():
                assert col._config is config 

    def test__getcol_global_file(self):
        x = self.tmpdir.ensure("x.py")
        config = py.test.config._reparse([x])
        col = config._getcollector(x)
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == self.tmpdir.basename 
        assert col.parent.parent is None
        for col in col.listchain():
            assert col._config is config 

    def test__getcol_global_dir(self):
        x = self.tmpdir.ensure("a", dir=1)
        config = py.test.config._reparse([x])
        col = config._getcollector(x)
        assert isinstance(col, py.test.collect.Directory)
        print col.listchain()
        assert col.name == 'a'
        assert col.parent is None
        assert col._config is config 

    def test__getcol_pkgfile(self):
        x = self.tmpdir.ensure("x.py")
        self.tmpdir.ensure("__init__.py")
        config = py.test.config._reparse([x])
        col = config._getcollector(x)
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == x.dirpath().basename 
        assert col.parent.parent is None
        for col in col.listchain():
            assert col._config is config 

    def test_get_collector_trail_and_back(self):
        a = self.tmpdir.ensure("a", dir=1)
        self.tmpdir.ensure("a", "__init__.py")
        x = self.tmpdir.ensure("a", "trail.py")
        config = py.test.config._reparse([x])
        col = config._getcollector(x)
        trail = config.get_collector_trail(col)
        assert len(trail) == 2
        assert trail[0] == a.relto(config.topdir)
        assert trail[1] == ('trail.py',)
        col2 = config._getcollector(trail)
        assert col2.listnames() == col.listnames()
       
    def test_get_collector_trail_topdir_and_beyond(self):
        config = py.test.config._reparse([self.tmpdir])
        col = config._getcollector(config.topdir)
        trail = config.get_collector_trail(col)
        assert len(trail) == 2
        assert trail[0] == '.'
        assert trail[1] == ()
        col2 = config._getcollector(trail)
        assert col2.fspath == config.topdir
        assert len(col2.listchain()) == 1
        col3 = config._getcollector(config.topdir.dirpath())
        py.test.raises(ValueError, 
              "config.get_collector_trail(col3)")

