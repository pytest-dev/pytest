import py

def pytest_funcarg__pickletransport(pyfuncitem):
    return ImmutablePickleTransport()

def pytest_pyfunc_call(__call__, pyfuncitem, args, kwargs):
    # for each function call we patch py._com.pyplugins
    # so that the unpickling of config objects 
    # (which bind to this mechanism) doesn't do harm 
    # usually config objects are no meant to be unpickled in
    # the same system 
    oldconfig = py.test.config 
    oldcom = py._com.pyplugins 
    print "setting py.test.config to None"
    py.test.config = None
    py._com.pyplugins = py._com.PyPlugins()
    try:
        return __call__.execute(firstresult=True)
    finally:
        print "setting py.test.config to", oldconfig
        py.test.config = oldconfig
        py._com.pyplugins = oldcom

class ImmutablePickleTransport:
    def __init__(self):
        from py.__.test.dist.mypickle import ImmutablePickler
        self.p1 = ImmutablePickler(uneven=0)
        self.p2 = ImmutablePickler(uneven=1)

    def p1_to_p2(self, obj):
        return self.p2.loads(self.p1.dumps(obj))

    def p2_to_p1(self, obj):
        return self.p1.loads(self.p2.dumps(obj))

    def unifyconfig(self, config):
        p2config = self.p1_to_p2(config)
        p2config._initafterpickle(config.topdir)
        return p2config

class TestImmutablePickling:
    def test_pickle_config(self, testdir, pickletransport):
        config1 = testdir.parseconfig()
        assert config1.topdir == testdir.tmpdir
        testdir.chdir()
        p2config = pickletransport.p1_to_p2(config1)
        assert p2config.topdir.realpath() == config1.topdir.realpath()
        config_back = pickletransport.p2_to_p1(p2config)
        assert config_back is config1

    def test_pickle_modcol(self, testdir, pickletransport):
        modcol1 = testdir.getmodulecol("def test_one(): pass")
        modcol2a = pickletransport.p1_to_p2(modcol1)
        modcol2b = pickletransport.p1_to_p2(modcol1)
        assert modcol2a is modcol2b

        modcol1_back = pickletransport.p2_to_p1(modcol2a)
        assert modcol1_back

    def test_pickle_func(self, testdir, pickletransport):
        modcol1 = testdir.getmodulecol("def test_one(): pass")
        item = modcol1.collect_by_name("test_one")
        testdir.chdir()
        item2a = pickletransport.p1_to_p2(item)
        assert item is not item2a # of course
        assert item2a.name == item.name
        modback = pickletransport.p2_to_p1(item2a.parent)
        assert modback is modcol1


class TestConfigPickling:
    def test_config_getstate_setstate(self, testdir):
        from py.__.test.config import Config
        testdir.makepyfile(__init__="", conftest="x=1; y=2")
        hello = testdir.makepyfile(hello="")
        tmp = testdir.tmpdir
        testdir.chdir()
        config1 = testdir.parseconfig(hello)
        config2 = Config()
        config2.__setstate__(config1.__getstate__())
        assert config2.topdir == py.path.local()
        config2_relpaths = [x.relto(config2.topdir) for x in config2.args]
        config1_relpaths = [x.relto(config1.topdir) for x in config1.args]

        assert config2_relpaths == config1_relpaths
        for name, value in config1.option.__dict__.items():
            assert getattr(config2.option, name) == value
        assert config2.getvalue("x") == 1

    def test_config_pickling_customoption(self, testdir):
        testdir.makeconftest("""
            class ConftestPlugin:
                def pytest_addoption(self, parser):
                    group = parser.addgroup("testing group")
                    group.addoption('-G', '--glong', action="store", default=42, 
                        type="int", dest="gdest", help="g value.")
        """)
        config = testdir.parseconfig("-G", "11")
        assert config.option.gdest == 11
        repr = config.__getstate__()

        config = testdir.Config()
        py.test.raises(AttributeError, "config.option.gdest")

        config2 = testdir.Config()
        config2.__setstate__(repr) 
        assert config2.option.gdest == 11

    def test_config_pickling_and_conftest_deprecated(self, testdir):
        tmp = testdir.tmpdir.ensure("w1", "w2", dir=1)
        tmp.ensure("__init__.py")
        tmp.join("conftest.py").write(py.code.Source("""
            class ConftestPlugin:
                def pytest_addoption(self, parser):
                    group = parser.addgroup("testing group")
                    group.addoption('-G', '--glong', action="store", default=42, 
                        type="int", dest="gdest", help="g value.")
        """))
        config = testdir.parseconfig(tmp, "-G", "11")
        assert config.option.gdest == 11
        repr = config.__getstate__()

        config = testdir.Config()
        py.test.raises(AttributeError, "config.option.gdest")

        config2 = testdir.Config()
        config2.__setstate__(repr) 
        assert config2.option.gdest == 11
       
        option = config2.addoptions("testing group", 
                config2.Option('-G', '--glong', action="store", default=42,
                       type="int", dest="gdest", help="g value."))
        assert option.gdest == 11

    def test_config_picklability(self, testdir):
        import cPickle
        config = testdir.parseconfig()
        s = cPickle.dumps(config)
        newconfig = cPickle.loads(s)
        assert hasattr(newconfig, "topdir")
        assert newconfig.topdir == py.path.local()

    def test_collector_implicit_config_pickling(self, testdir):
        from cPickle import Pickler, Unpickler
        tmpdir = testdir.tmpdir
        testdir.chdir()
        testdir.makepyfile(hello="def test_x(): pass")
        config = testdir.parseconfig(tmpdir)
        col = config.getfsnode(config.topdir)
        io = py.std.cStringIO.StringIO()
        pickler = Pickler(io)
        pickler.dump(col)
        io.seek(0) 
        unpickler = Unpickler(io)
        col2 = unpickler.load()
        assert col2.name == col.name 
        assert col2.listnames() == col.listnames()

    def test_config_and_collector_pickling(self, testdir):
        from cPickle import Pickler, Unpickler
        tmpdir = testdir.tmpdir
        dir1 = tmpdir.ensure("somedir", dir=1)
        config = testdir.parseconfig()
        col = config.getfsnode(config.topdir)
        col1 = col.join(dir1.basename)
        assert col1.parent is col 
        io = py.std.cStringIO.StringIO()
        pickler = Pickler(io)
        pickler.dump(col)
        pickler.dump(col1)
        pickler.dump(col)
        io.seek(0) 
        unpickler = Unpickler(io)
        topdir = tmpdir.ensure("newtopdir", dir=1)
        topdir.ensure("somedir", dir=1)
        old = topdir.chdir()
        try:
            newcol = unpickler.load()
            newcol2 = unpickler.load()
            newcol3 = unpickler.load()
            assert newcol2.config is newcol.config
            assert newcol2.parent == newcol 
            assert newcol2.config.topdir.realpath() == topdir.realpath()
            assert newcol.fspath.realpath() == topdir.realpath()
            assert newcol2.fspath.basename == dir1.basename
            assert newcol2.fspath.relto(newcol2.config.topdir)
        finally:
            old.chdir() 

def test_config__setstate__wired_correctly_in_childprocess(testdir):
    from py.__.test.dist.mypickle import PickleChannel
    gw = py.execnet.PopenGateway()
    channel = gw.remote_exec("""
        import py
        from py.__.test.dist.mypickle import PickleChannel
        channel = PickleChannel(channel)
        config = channel.receive()
        assert py.test.config.pytestplugins.pyplugins == py._com.pyplugins, "pyplugins wrong"
        assert py.test.config.bus == py._com.pyplugins, "bus wrong"
    """)
    channel = PickleChannel(channel)
    config = testdir.parseconfig()
    channel.send(config)
    channel.waitclose() # this will raise 
    gw.exit()
    

