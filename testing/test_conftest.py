import py, pytest
from _pytest.config import Conftest

def pytest_generate_tests(metafunc):
    if "basedir" in metafunc.funcargnames:
        metafunc.addcall(param="global")
        metafunc.addcall(param="inpackage")

def pytest_funcarg__basedir(request):
    def basedirmaker(request):
        basedir = d = request.getfuncargvalue("tmpdir")
        d.ensure("adir/conftest.py").write("a=1 ; Directory = 3")
        d.ensure("adir/b/conftest.py").write("b=2 ; a = 1.5")
        if request.param == "inpackage":
            d.ensure("adir/__init__.py")
            d.ensure("adir/b/__init__.py")
        return d
    return request.cached_setup(lambda: basedirmaker(request), extrakey=request.param)

def ConftestWithSetinitial(path):
    conftest = Conftest()
    conftest.setinitial([path])
    return conftest

class TestConftestValueAccessGlobal:
    def test_basic_init(self, basedir):
        conftest = Conftest()
        conftest.setinitial([basedir.join("adir")])
        assert conftest.rget("a") == 1

    def test_onimport(self, basedir):
        l = []
        conftest = Conftest(onimport=l.append)
        conftest.setinitial([basedir.join("adir"),
            '--confcutdir=%s' % basedir])
        assert len(l) == 1
        assert conftest.rget("a") == 1
        assert conftest.rget("b", basedir.join("adir", "b")) == 2
        assert len(l) == 2

    def test_immediate_initialiation_and_incremental_are_the_same(self, basedir):
        conftest = Conftest()
        snap0 = len(conftest._path2confmods)
        conftest.getconftestmodules(basedir)
        snap1 = len(conftest._path2confmods)
        #assert len(conftest._path2confmods) == snap1 + 1
        conftest.getconftestmodules(basedir.join('adir'))
        assert len(conftest._path2confmods) == snap1 + 1
        conftest.getconftestmodules(basedir.join('b'))
        assert len(conftest._path2confmods) == snap1 + 2

    def test_default_has_lower_prio(self, basedir):
        conftest = ConftestWithSetinitial(basedir.join("adir"))
        assert conftest.rget('Directory') == 3
        #assert conftest.lget('Directory') == pytest.Directory

    def test_value_access_not_existing(self, basedir):
        conftest = ConftestWithSetinitial(basedir)
        pytest.raises(KeyError, "conftest.rget('a')")
        #pytest.raises(KeyError, "conftest.lget('a')")

    def test_value_access_by_path(self, basedir):
        conftest = ConftestWithSetinitial(basedir)
        assert conftest.rget("a", basedir.join('adir')) == 1
        #assert conftest.lget("a", basedir.join('adir')) == 1
        assert conftest.rget("a", basedir.join('adir', 'b')) == 1.5
        #assert conftest.lget("a", basedir.join('adir', 'b')) == 1
        #assert conftest.lget("b", basedir.join('adir', 'b')) == 2
        #assert pytest.raises(KeyError,
        #    'conftest.lget("b", basedir.join("a"))'
        #)

    def test_value_access_with_init_one_conftest(self, basedir):
        conftest = ConftestWithSetinitial(basedir.join('adir'))
        assert conftest.rget("a") == 1
        #assert conftest.lget("a") == 1

    def test_value_access_with_init_two_conftests(self, basedir):
        conftest = ConftestWithSetinitial(basedir.join("adir", "b"))
        conftest.rget("a") == 1.5
        #conftest.lget("a") == 1
        #conftest.lget("b") == 1

    def test_value_access_with_confmod(self, basedir):
        startdir = basedir.join("adir", "b")
        startdir.ensure("xx", dir=True)
        conftest = ConftestWithSetinitial(startdir)
        mod, value = conftest.rget_with_confmod("a", startdir)
        assert  value == 1.5
        path = py.path.local(mod.__file__)
        assert path.dirpath() == basedir.join("adir", "b")
        assert path.purebasename.startswith("conftest")

def test_conftest_in_nonpkg_with_init(tmpdir):
    tmpdir.ensure("adir-1.0/conftest.py").write("a=1 ; Directory = 3")
    tmpdir.ensure("adir-1.0/b/conftest.py").write("b=2 ; a = 1.5")
    tmpdir.ensure("adir-1.0/b/__init__.py")
    tmpdir.ensure("adir-1.0/__init__.py")
    conftest = ConftestWithSetinitial(tmpdir.join("adir-1.0", "b"))

def test_doubledash_not_considered(testdir):
    conf = testdir.mkdir("--option")
    conf.join("conftest.py").ensure()
    conftest = Conftest()
    conftest.setinitial([conf.basename, conf.basename])
    l = conftest.getconftestmodules(None)
    assert len(l) == 0

def test_conftest_global_import(testdir):
    testdir.makeconftest("x=3")
    p = testdir.makepyfile("""
        import py, pytest
        from _pytest.config import Conftest
        conf = Conftest()
        mod = conf.importconftest(py.path.local("conftest.py"))
        assert mod.x == 3
        import conftest
        assert conftest is mod, (conftest, mod)
        subconf = py.path.local().ensure("sub", "conftest.py")
        subconf.write("y=4")
        mod2 = conf.importconftest(subconf)
        assert mod != mod2
        assert mod2.y == 4
        import conftest
        assert conftest is mod2, (conftest, mod)
    """)
    res = testdir.runpython(p)
    assert res.ret == 0

def test_conftestcutdir(testdir):
    conf = testdir.makeconftest("")
    p = testdir.mkdir("x")
    conftest = Conftest(confcutdir=p)
    conftest.setinitial([testdir.tmpdir])
    l = conftest.getconftestmodules(p)
    assert len(l) == 0
    l = conftest.getconftestmodules(conf.dirpath())
    assert len(l) == 0
    assert conf not in conftest._conftestpath2mod
    # but we can still import a conftest directly
    conftest.importconftest(conf)
    l = conftest.getconftestmodules(conf.dirpath())
    assert l[0].__file__.startswith(str(conf))
    # and all sub paths get updated properly
    l = conftest.getconftestmodules(p)
    assert len(l) == 1
    assert l[0].__file__.startswith(str(conf))

def test_conftestcutdir_inplace_considered(testdir):
    conf = testdir.makeconftest("")
    conftest = Conftest(confcutdir=conf.dirpath())
    conftest.setinitial([conf.dirpath()])
    l = conftest.getconftestmodules(conf.dirpath())
    assert len(l) == 1
    assert l[0].__file__.startswith(str(conf))

def test_setinitial_confcut(testdir):
    conf = testdir.makeconftest("")
    sub = testdir.mkdir("sub")
    sub.chdir()
    for opts in (["--confcutdir=%s" % sub, sub],
                [sub, "--confcutdir=%s" % sub],
                ["--confcutdir=.", sub],
                [sub, "--confcutdir", sub],
                [str(sub), "--confcutdir", "."],
    ):
        conftest = Conftest()
        conftest.setinitial(opts)
        assert conftest._confcutdir == sub
        assert conftest.getconftestmodules(sub) == []
        assert conftest.getconftestmodules(conf.dirpath()) == []

@pytest.mark.multi(name='test tests whatever .dotdir'.split())
def test_setinitial_conftest_subdirs(testdir, name):
    sub = testdir.mkdir(name)
    subconftest = sub.ensure("conftest.py")
    conftest = Conftest()
    conftest.setinitial([sub.dirpath(), '--confcutdir=%s' % testdir.tmpdir])
    if name not in ('whatever', '.dotdir'):
        assert  subconftest in conftest._conftestpath2mod
        assert len(conftest._conftestpath2mod) == 1
    else:
        assert  subconftest not in conftest._conftestpath2mod
        assert len(conftest._conftestpath2mod) == 0

def test_conftest_confcutdir(testdir):
    testdir.makeconftest("assert 0")
    x = testdir.mkdir("x")
    x.join("conftest.py").write(py.code.Source("""
        def pytest_addoption(parser):
            parser.addoption("--xyz", action="store_true")
    """))
    result = testdir.runpytest("-h", "--confcutdir=%s" % x, x)
    result.stdout.fnmatch_lines(["*--xyz*"])
