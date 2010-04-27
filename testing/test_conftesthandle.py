import py
from py._test.conftesthandle import Conftest

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
        conftest.setinitial([basedir.join("adir")])
        assert len(l) == 2 
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
        #assert conftest.lget('Directory') == py.test.collect.Directory 
        
    def test_value_access_not_existing(self, basedir):
        conftest = ConftestWithSetinitial(basedir)
        py.test.raises(KeyError, "conftest.rget('a')")
        #py.test.raises(KeyError, "conftest.lget('a')")

    def test_value_access_by_path(self, basedir):
        conftest = ConftestWithSetinitial(basedir)
        assert conftest.rget("a", basedir.join('adir')) == 1
        #assert conftest.lget("a", basedir.join('adir')) == 1
        assert conftest.rget("a", basedir.join('adir', 'b')) == 1.5 
        #assert conftest.lget("a", basedir.join('adir', 'b')) == 1
        #assert conftest.lget("b", basedir.join('adir', 'b')) == 2
        #assert py.test.raises(KeyError, 
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
        topdir = basedir.join("adir", "b")
        topdir.ensure("xx", dir=True)
        conftest = ConftestWithSetinitial(topdir)
        mod, value = conftest.rget_with_confmod("a", topdir)
        assert  value == 1.5
        path = py.path.local(mod.__file__)
        assert path.dirpath() == basedir.join("adir", "b")
        assert path.purebasename == "conftest"

def test_conftest_in_nonpkg_with_init(tmpdir):
    tmpdir.ensure("adir-1.0/conftest.py").write("a=1 ; Directory = 3")
    tmpdir.ensure("adir-1.0/b/conftest.py").write("b=2 ; a = 1.5")
    tmpdir.ensure("adir-1.0/b/__init__.py")
    tmpdir.ensure("adir-1.0/__init__.py")
    conftest = ConftestWithSetinitial(tmpdir.join("adir-1.0", "b"))

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

@py.test.mark.multi(name='test tests whatever .dotdir'.split())
def test_setinitial_conftest_subdirs(testdir, name):
    sub = testdir.mkdir(name)
    subconftest = sub.ensure("conftest.py")
    conftest = Conftest()
    conftest.setinitial([sub.dirpath()])
    if name != ".dotdir":
        assert  subconftest in conftest._conftestpath2mod
        assert len(conftest._conftestpath2mod) == 1
    else:
        assert  subconftest not in conftest._conftestpath2mod
        assert len(conftest._conftestpath2mod) == 0
