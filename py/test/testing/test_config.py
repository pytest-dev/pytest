from __future__ import generators
import py

from py.__.test.config import gettopdir
from py.__.test.testing import suptest
from py.__.test import event

def getcolitems(config):
    return [config.getfsnode(arg) for arg in config.args]
    
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
    o = o.mkdir("onemore") # neccessary because collection of o.dirpath()
                           # could see our conftest.py
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
    somefile = tmp.ensure("somefile.py")
    assert gettopdir([somefile]) == tmp

def test_gettopdir_pypkg():
    tmp = py.test.ensuretemp("topdir2")
    a = tmp.ensure('a', dir=1)
    b = tmp.ensure('a', 'b', '__init__.py')
    c = tmp.ensure('a', 'b', 'c.py')
    Z = tmp.ensure('Z', dir=1)
    assert gettopdir([c]) == a
    assert gettopdir([c, Z]) == tmp 


def test_config_initafterpickle_some():
    tmp = py.test.ensuretemp("test_config_initafterpickle_some")
    tmp.ensure("__init__.py")
    tmp.ensure("conftest.py").write("x=1 ; y=2")
    hello = tmp.ensure("test_hello.py")
    config = py.test.config._reparse([hello])
    config2 = py.test.config._reparse([tmp.dirpath()])
    config2._initialized = False # we have to do that from tests
    config2._repr = config._makerepr()
    config2._initafterpickle(topdir=tmp.dirpath())
    for col1, col2 in zip(getcolitems(config), getcolitems(config2)):
        assert col1.fspath == col2.fspath
    cols = getcolitems(config2)
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
    repr = config._makerepr()
    config.option.verbose = 42
    repr2 = config._makerepr()
    config = py.test.config._reparse([tmp.dirpath()])
    py.test.raises(KeyError, "config.getvalue('x')")
    config._mergerepr(repr)
    assert config.getvalue('x') == 1
    config._mergerepr(repr2) 
    assert config.option.verbose == 42

    
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
    repr = config._makerepr()
    config = py.test.config._reparse([tmp.dirpath()])
    py.test.raises(AttributeError, "config.option.gdest")
    config._mergerepr(repr) 
    option = config.addoptions("testing group", 
            config.Option('-G', '--glong', action="store", default=42,
                   type="int", dest="gdest", help="g value."))
    assert config.option.gdest == 11
    assert option.gdest == 11

class TestSessionAndOptions(suptest.FileCreation): 
    def exampletestfile(self):
        return self.makepyfile(file_test="""
            def test_one(): 
                assert 42 == 43

            class TestClass(object): 
                def test_method_one(self): 
                    assert 42 == 43 
        """)

    def test_session_eventlog(self):
        eventlog = self.tmpdir.join("test_session_eventlog")
        config = py.test.config._reparse([self.tmpdir, 
                                          '--eventlog=%s' % eventlog])
        session = config.initsession()
        session.bus.notify(event.TestrunStart())
        s = eventlog.read()
        assert s.find("TestrunStart") != -1

    def test_session_resultlog(self):
        from py.__.test.collect import Item
        from py.__.test.runner import OutcomeRepr

        resultlog = self.tmpdir.join("test_session_resultlog")
        config = py.test.config._reparse([self.tmpdir, 
                                          '--resultlog=%s' % resultlog])

        session = config.initsession()

        item = Item("a", config=config)
        outcome = OutcomeRepr('execute', '.', '')
        rep_ev = event.ItemTestReport(item, passed=outcome)
      
        session.bus.notify(rep_ev)
        
        s = resultlog.read()
        assert s.find(". a") != -1        

    def test_tracedir_tracer(self):
        tracedir = self.tmpdir.join("tracedir")
        config = py.test.config._reparse([self.tmpdir, 
                                          '--tracedir=%s' % tracedir])
        assert config.gettracedir() == tracedir

        trace = config.maketrace("trace1.log") # flush=True by default
        trace("hello", "world")
        class A: pass 
        trace(A())
        p = tracedir.join("trace1.log")
        lines = p.readlines(cr=0)
        assert lines[0].endswith("hello world")
        assert lines[1].find("A") != -1
        trace.close()

    def test_trace_null(self):
        config = py.test.config._reparse([self.tmpdir])
        assert config.gettracedir() is None
        trace = config.maketrace("hello", flush=True)
        trace("hello", "world")
        trace.close()

    def test_implied_dsession(self):
        for x in 'startserver runbrowser rest'.split():
            config = py.test.config._reparse([self.tmpdir, '--dist', '--%s' % x])
            assert config._getsessionname() == 'DSession'

    def test_implied_different_sessions(self):
        config = py.test.config._reparse([self.tmpdir])
        assert config._getsessionname() == 'Session'
        config = py.test.config._reparse([self.tmpdir, '--dist'])
        assert config._getsessionname() == 'DSession'
        config = py.test.config._reparse([self.tmpdir, '-n3'])
        assert config._getsessionname() == 'DSession'
        config = py.test.config._reparse([self.tmpdir, '--looponfailing'])
        assert config._getsessionname() == 'LooponfailingSession'
        config = py.test.config._reparse([self.tmpdir, '--exec=x'])
        assert config._getsessionname() == 'DSession'
        config = py.test.config._reparse([self.tmpdir, '--dist', '--exec=x'])
        assert config._getsessionname() == 'DSession'
        config = py.test.config._reparse([self.tmpdir, '-f', 
                                          '--dist', '--exec=x'])
        assert config._getsessionname() == 'LooponfailingSession'
        config = py.test.config._reparse([self.tmpdir, '-f', '-n3',
                                          '--dist', '--exec=x', 
                                          '--collectonly'])
        assert config._getsessionname() == 'Session'

    def test_sessionname_lookup_custom(self):
        self.tmpdir.join("conftest.py").write(py.code.Source("""
            from py.__.test.session import Session
            class MySession(Session):
                pass
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

    def test_boxed_option_from_conftest(self):
        tmpdir = self.tmpdir
        tmpdir.join("conftest.py").write(py.code.Source("""
            dist_boxed = False
        """))
        config = py.test.config._reparse([tmpdir, '--box'])
        assert config.option.boxed 
        config.initsession()
        assert config.option.boxed

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
        config = py.test.config._reparse([self.tmpdir])
        assert config.getvalue("conf_iocapture")
        tmpdir = self.tmpdir.ensure("sub-with-conftest", dir=1)
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

    def test_conflict_options(self):
        def check_conflict_option(opts):
            print "testing if options conflict:", " ".join(opts)
            path = self.exampletestfile()
            config = py.test.config._reparse(opts + [path])
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
    
    def test_implied_options(self):
        def check_implied_option(opts, expr):
            path = self.exampletestfile()
            config = py.test.config._reparse(opts + [path])
            session = config.initsession()
            assert eval(expr, session.config.option.__dict__)

        implied_options = {
            '-v': 'verbose', 
            '-l': 'showlocals',
            #'--runbrowser': 'startserver and runbrowser', XXX starts browser
        }
        for key, expr in implied_options.items():
            yield check_implied_option, [key], expr

    def test_default_session_options(self):
        def runfiletest(opts):
            sorter = suptest.events_from_cmdline(opts)
            passed, skipped, failed = sorter.countoutcomes()
            assert failed == 2 
            assert skipped == passed == 0
        path = self.exampletestfile()
        for opts in ([], ['-l'], ['-s'], ['--tb=no'], ['--tb=short'], 
                     ['--tb=long'], ['--fulltrace'], ['--nomagic'], 
                     ['--traceconfig'], ['-v'], ['-v', '-v']):
            yield runfiletest, opts + [path]

    def test_is_not_boxed_by_default(self):
        path = self.exampletestfile()
        config = py.test.config._reparse([path])
        assert not config.option.boxed


class TestConfigColitems(suptest.FileCreation):
    def setup_class(cls):
        cls.tmproot = py.test.ensuretemp(cls.__name__)

    def setup_method(self, method):
        self.tmpdir = self.tmproot.mkdir(method.__name__) 
    
    def test_getcolitems_onedir(self):
        config = py.test.config._reparse([self.tmpdir])
        colitems = getcolitems(config)
        assert len(colitems) == 1
        col = colitems[0]
        assert isinstance(col, py.test.collect.Directory)
        for col in col.listchain():
            assert col._config is config 

    def test_getcolitems_twodirs(self):
        config = py.test.config._reparse([self.tmpdir, self.tmpdir])
        colitems = getcolitems(config)
        assert len(colitems) == 2
        col1, col2 = colitems 
        assert col1.name == col2.name 
        assert col1.parent == col2.parent 

    def test_getcolitems_curdir_and_subdir(self):
        a = self.tmpdir.ensure("a", dir=1)
        config = py.test.config._reparse([self.tmpdir, a])
        colitems = getcolitems(config)
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
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == self.tmpdir.basename 
        assert col.parent.parent is None
        for col in col.listchain():
            assert col._config is config 

    def test__getcol_global_dir(self):
        x = self.tmpdir.ensure("a", dir=1)
        config = py.test.config._reparse([x])
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Directory)
        print col.listchain()
        assert col.name == 'a'
        assert col.parent is None
        assert col._config is config 

    def test__getcol_pkgfile(self):
        x = self.tmpdir.ensure("x.py")
        self.tmpdir.ensure("__init__.py")
        config = py.test.config._reparse([x])
        col = config.getfsnode(x)
        assert isinstance(col, py.test.collect.Module)
        assert col.name == 'x.py'
        assert col.parent.name == x.dirpath().basename 
        assert col.parent.parent is None
        for col in col.listchain():
            assert col._config is config 


    def test_config_picklability(self):
        import cPickle
        config = py.test.config._reparse([self.tmpdir])
        s = cPickle.dumps(config)
        newconfig = cPickle.loads(s)
        assert not hasattr(newconfig, "topdir")
        assert not newconfig._initialized 
        assert not hasattr(newconfig, 'args')
        newconfig._initafterpickle(config.topdir)
        assert newconfig.topdir == config.topdir 
        assert newconfig._initialized 
        assert newconfig.args == [self.tmpdir]

    def test_config_and_collector_pickling_missing_initafter(self):
        from cPickle import Pickler, Unpickler
        config = py.test.config._reparse([self.tmpdir])
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

    def test_config_and_collector_pickling(self):
        from cPickle import Pickler, Unpickler
        dir1 = self.tmpdir.ensure("somedir", dir=1)
        config = py.test.config._reparse([self.tmpdir])
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
        topdir = self.tmpdir.ensure("newtopdir", dir=1)
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

