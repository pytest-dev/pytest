import py

class TestConfigCmdlineParsing:
    def test_config_cmdline_options(self, testdir):
        testdir.makepyfile(conftest="""
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
            """)
        testdir.chdir() 
        config = py.test.config._reparse(['-G', '17'])
        assert config.option.gdest == 17 

    def test_config_cmdline_options_only_lowercase(self, testdir): 
        testdir.makepyfile(conftest="""
            import py
            Option = py.test.config.Option
            options = py.test.config.addoptions("testing group", 
                Option('-g', '--glong', action="store", default=42,
                       type="int", dest="gdest", help="g value."), 
                )
        """)
        old = testdir.chdir()
        try: 
            py.test.raises(ValueError, """
                py.test.config._reparse(['-g', '17'])
            """)
        finally: 
            old.chdir() 

    def test_parsing_again_fails(self, tmpdir):
        config = py.test.config._reparse([tmpdir])
        py.test.raises(AssertionError, "config.parse([])")

    def test_conflict_options(self):
        def check_conflict_option(opts):
            print "testing if options conflict:", " ".join(opts)
            config = py.test.config._reparse(opts)
            py.test.raises((ValueError, SystemExit), """
                config.initsession()
            """)
        py.test.skip("check on conflict options")
        conflict_options = (
            '--looponfailing --pdb',
            '--dist --pdb', 
            '--exec=%s --pdb' % (py.std.sys.executable,),
        )
        for spec in conflict_options: 
            opts = spec.split()
            yield check_conflict_option, opts

class TestConfigAPI: 
    @py.test.mark.issue("ensuretemp should call config.maketemp(basename)")
    def test_tmpdir(self):
        d1 = py.test.ensuretemp('hello') 
        d2 = py.test.ensuretemp('hello') 
        assert d1 == d2
        assert d1.check(dir=1) 

    def test_config_getvalue_honours_conftest(self, testdir):
        testdir.makepyfile(conftest="x=1")
        testdir.mkdir("sub").join("conftest.py").write("x=2 ; y = 3")
        config = testdir.parseconfig()
        o = testdir.tmpdir
        assert config.getvalue("x") == 1
        assert config.getvalue("x", o.join('sub')) == 2
        py.test.raises(KeyError, "config.getvalue('y')")
        config = py.test.config._reparse([str(o.join('sub'))])
        assert config.getvalue("x") == 2
        assert config.getvalue("y") == 3
        assert config.getvalue("x", o) == 1
        py.test.raises(KeyError, 'config.getvalue("y", o)')

    def test_config_overwrite(self, testdir):
        o = testdir.tmpdir
        o.ensure("conftest.py").write("x=1")
        config = py.test.config._reparse([str(o)])
        assert config.getvalue('x') == 1
        config.option.x = 2
        assert config.getvalue('x') == 2
        config = py.test.config._reparse([str(o)])
        assert config.getvalue('x') == 1

    def test_getvalue_pathlist(self, tmpdir):
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

    def test_setsessionclass_and_initsession(self, testdir):
        from py.__.test.config import Config 
        config = Config()
        class Session1: 
            def __init__(self, config):
                self.config = config 
        config.setsessionclass(Session1)
        session = config.initsession()
        assert isinstance(session, Session1)
        assert session.config is config
        py.test.raises(ValueError, "config.setsessionclass(Session1)")



class TestConfigApi_getcolitems:
    def test_getcolitems_onedir(self, tmpdir):
        config = py.test.config._reparse([tmpdir])
        colitems = config.getcolitems()
        assert len(colitems) == 1
        col = colitems[0]
        assert isinstance(col, py.test.collect.Directory)
        for col in col.listchain():
            assert col._config is config 

    def test_getcolitems_twodirs(self, tmpdir):
        config = py.test.config._reparse([tmpdir, tmpdir])
        colitems = config.getcolitems()
        assert len(colitems) == 2
        col1, col2 = colitems 
        assert col1.name == col2.name 
        assert col1.parent == col2.parent 

    def test_getcolitems_curdir_and_subdir(self, tmpdir):
        a = tmpdir.ensure("a", dir=1)
        config = py.test.config._reparse([tmpdir, a])
        colitems = config.getcolitems()
        assert len(colitems) == 2
        col1, col2 = colitems 
        assert col1.name == tmpdir.basename
        assert col2.name == 'a'
        for col in colitems:
            for subcol in col.listchain():
                assert col._config is config 

    def test__getcol_global_file(self, tmpdir):
        x = tmpdir.ensure("x.py")
        config = py.test.config._reparse([x])
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == tmpdir.basename 
        assert col.parent.parent is None
        for col in col.listchain():
            assert col._config is config 

    def test__getcol_global_dir(self, tmpdir):
        x = tmpdir.ensure("a", dir=1)
        config = py.test.config._reparse([x])
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Directory)
        print col.listchain()
        assert col.name == 'a'
        assert col.parent is None
        assert col._config is config 

    def test__getcol_pkgfile(self, tmpdir):
        x = tmpdir.ensure("x.py")
        tmpdir.ensure("__init__.py")
        config = py.test.config._reparse([x])
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == x.dirpath().basename 
        assert col.parent.parent is None
        for col in col.listchain():
            assert col._config is config 




class TestOptionEffects:
    def test_boxed_option_default(self, testdir):
        testdir.makepyfile(conftest="dist_hosts=[]")
        tmpdir = testdir.tmpdir.ensure("subdir", dir=1)
        config = py.test.config._reparse([tmpdir])
        config.initsession()
        assert not config.option.boxed
        config = py.test.config._reparse(['--dist', tmpdir])
        config.initsession()
        assert not config.option.boxed

    def test_is_not_boxed_by_default(self, testdir):
        config = py.test.config._reparse([testdir.tmpdir])
        assert not config.option.boxed

    def test_boxed_option_from_conftest(self, testdir):
        testdir.makepyfile(conftest="dist_hosts=[]")
        tmpdir = testdir.tmpdir.ensure("subdir", dir=1)
        tmpdir.join("conftest.py").write(py.code.Source("""
            dist_hosts = []
            dist_boxed = True
        """))
        config = py.test.config._reparse(['--dist', tmpdir])
        config.initsession()
        assert config.option.boxed 

    def test_boxed_option_from_conftest(self, testdir):
        testdir.makepyfile(conftest="dist_boxed=False")
        config = py.test.config._reparse([testdir.tmpdir, '--box'])
        assert config.option.boxed 
        config.initsession()
        assert config.option.boxed

    def test_config_iocapturing(self, testdir):
        config = testdir.parseconfig(testdir.tmpdir)
        assert config.getvalue("conf_iocapture")
        tmpdir = testdir.tmpdir.ensure("sub-with-conftest", dir=1)
        tmpdir.join("conftest.py").write(py.code.Source("""
            conf_iocapture = "no"
        """))
        config = py.test.config._reparse([tmpdir])
        assert config.getvalue("conf_iocapture") == "no"
        capture = config._getcapture()
        assert isinstance(capture, py.io.StdCapture)
        assert not capture._out
        assert not capture._err
        assert not capture._in
        assert isinstance(capture, py.io.StdCapture)
        for opt, cls in (("sys", py.io.StdCapture),  
                         ("fd", py.io.StdCaptureFD), 
                        ):
            config.option.conf_iocapture = opt
            capture = config._getcapture()
            assert isinstance(capture, cls) 


class TestConfig_gettopdir:
    def test_gettopdir(self, testdir):
        from py.__.test.config import gettopdir
        tmp = testdir.tmpdir
        assert gettopdir([tmp]) == tmp
        topdir = gettopdir([tmp.join("hello"), tmp.join("world")])
        assert topdir == tmp 
        somefile = tmp.ensure("somefile.py")
        assert gettopdir([somefile]) == tmp

    def test_gettopdir_pypkg(self, testdir):
        from py.__.test.config import gettopdir
        tmp = testdir.tmpdir
        a = tmp.ensure('a', dir=1)
        b = tmp.ensure('a', 'b', '__init__.py')
        c = tmp.ensure('a', 'b', 'c.py')
        Z = tmp.ensure('Z', dir=1)
        assert gettopdir([c]) == a
        assert gettopdir([c, Z]) == tmp 

class TestConfigPickling:
    @py.test.mark(xfail=True, issue="config's pytestplugins/bus initialization")
    def test_config_initafterpickle_plugin(self, testdir):
        testdir.makepyfile(__init__="", conftest="x=1; y=2")
        hello = testdir.makepyfile(hello="")
        tmp = testdir.tmpdir
        config = py.test.config._reparse([hello])
        config2 = py.test.config._reparse([tmp.dirpath()])
        config2._initialized = False # we have to do that from tests
        config2._repr = config._makerepr()
        config2._initafterpickle(topdir=tmp.dirpath())
        # we check that config "remote" config objects 
        # have correct plugin initialization 
        #XXX assert config2.pytestplugins.pm._plugins
        #XXX assert config2.bus.isregistered(config2.pytestplugins.forward_event)
        assert config2.bus == py._com.pyplugins 
        assert config2.pytestplugins.pm == py._com.pyplugins 

    def test_config_initafterpickle_some(self, testdir):
        tmp = testdir.tmpdir
        tmp.ensure("__init__.py")
        tmp.ensure("conftest.py").write("x=1 ; y=2")
        hello = tmp.ensure("test_hello.py")
        config = py.test.config._reparse([hello])
        config2 = py.test.config._reparse([tmp.dirpath()])
        config2._initialized = False # we have to do that from tests
        config2._repr = config._makerepr()
        config2._initafterpickle(topdir=tmp.dirpath())

        for col1, col2 in zip(config.getcolitems(), config2.getcolitems()):
            assert col1.fspath == col2.fspath
        cols = config2.getcolitems()
        assert len(cols) == 1
        col = cols[0]
        assert col.name == 'test_hello.py'
        assert col.parent.name == tmp.basename 
        assert col.parent.parent is None 

    def test_config_make_and__mergerepr(self, testdir):
        tmp = testdir.tmpdir
        tmp.ensure("__init__.py")
        tmp.ensure("conftest.py").write("x=1")
        config = py.test.config._reparse([tmp])
        repr = config._makerepr()
        config.option.verbose = 42
        repr2 = config._makerepr()
        config = py.test.config._reparse([tmp.dirpath()])
        py.test.raises(KeyError, "config.getvalue('x')")
        config._mergerepr(repr)
        assert config.getvalue('x') == 1
        config._mergerepr(repr2) 
        assert config.option.verbose == 42
        
    def test_config_rconfig(self, testdir):
        tmp = testdir.tmpdir
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
        repr = config._makerepr()
        config = py.test.config._reparse([tmp.dirpath()])
        py.test.raises(AttributeError, "config.option.gdest")
        config._mergerepr(repr) 
        option = config.addoptions("testing group", 
                config.Option('-G', '--glong', action="store", default=42,
                       type="int", dest="gdest", help="g value."))
        assert config.option.gdest == 11
        assert option.gdest == 11

    def test_config_picklability(self, tmpdir):
        import cPickle
        config = py.test.config._reparse([tmpdir])
        s = cPickle.dumps(config)
        newconfig = cPickle.loads(s)
        assert not hasattr(newconfig, "topdir")
        assert not newconfig._initialized 
        assert not hasattr(newconfig, 'args')
        newconfig._initafterpickle(config.topdir)
        assert newconfig.topdir == config.topdir 
        assert newconfig._initialized 
        assert newconfig.args == [tmpdir]

    def test_config_and_collector_pickling_missing_initafter(self, tmpdir):
        from cPickle import Pickler, Unpickler
        config = py.test.config._reparse([tmpdir])
        col = config.getfsnode(config.topdir)
        io = py.std.cStringIO.StringIO()
        pickler = Pickler(io)
        pickler.dump(config)
        pickler.dump(col)
        io.seek(0) 
        unpickler = Unpickler(io)
        newconfig = unpickler.load()
        # we don't call _initafterpickle ... so
        py.test.raises(ValueError, "unpickler.load()")

    def test_config_and_collector_pickling(self, tmpdir):
        from cPickle import Pickler, Unpickler
        dir1 = tmpdir.ensure("somedir", dir=1)
        config = py.test.config._reparse([tmpdir])
        col = config.getfsnode(config.topdir)
        col1 = col.join(dir1.basename)
        assert col1.parent is col 
        io = py.std.cStringIO.StringIO()
        pickler = Pickler(io)
        pickler.dump(config)
        pickler.dump(col)
        pickler.dump(col1)
        pickler.dump(col)
        io.seek(0) 
        unpickler = Unpickler(io)
        newconfig = unpickler.load()
        topdir = tmpdir.ensure("newtopdir", dir=1)
        newconfig._initafterpickle(topdir)
        topdir.ensure("somedir", dir=1)
        newcol = unpickler.load()
        newcol2 = unpickler.load()
        newcol3 = unpickler.load()
        assert newcol2._config is newconfig 
        assert newcol2.parent == newcol 
        assert newcol._config is newconfig
        assert newconfig.topdir == topdir
        assert newcol3 is newcol
        assert newcol.fspath == topdir 
        assert newcol2.fspath.basename == dir1.basename
        assert newcol2.fspath.relto(topdir)

def test_options_on_small_file_do_not_blow_up(testdir):
    def runfiletest(opts):
        sorter = testdir.inline_run(*opts)
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 2 
        assert skipped == passed == 0
    path = testdir.makepyfile("""
        def test_f1(): assert 0
        def test_f2(): assert 0
    """)

    for opts in ([], ['-l'], ['-s'], ['--tb=no'], ['--tb=short'], 
                 ['--tb=long'], ['--fulltrace'], ['--nomagic'], 
                 ['--traceconfig'], ['-v'], ['-v', '-v']):
        runfiletest(opts + [path])

def test_default_bus():
    assert py.test.config.bus is py._com.pyplugins
    
