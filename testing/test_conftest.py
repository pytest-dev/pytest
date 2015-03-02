from textwrap import dedent
import py, pytest
from _pytest.config import Conftest



@pytest.fixture(scope="module", params=["global", "inpackage"])
def basedir(request):
    from _pytest.tmpdir import tmpdir
    tmpdir = tmpdir(request)
    tmpdir.ensure("adir/conftest.py").write("a=1 ; Directory = 3")
    tmpdir.ensure("adir/b/conftest.py").write("b=2 ; a = 1.5")
    if request.param == "inpackage":
        tmpdir.ensure("adir/__init__.py")
        tmpdir.ensure("adir/b/__init__.py")
    return tmpdir

def ConftestWithSetinitial(path):
    conftest = Conftest()
    conftest_setinitial(conftest, [path])
    return conftest

def conftest_setinitial(conftest, args, confcutdir=None):
    class Namespace:
        def __init__(self):
            self.file_or_dir = args
            self.confcutdir = str(confcutdir)
    conftest.setinitial(Namespace())

class TestConftestValueAccessGlobal:
    def test_basic_init(self, basedir):
        conftest = Conftest()
        p = basedir.join("adir")
        assert conftest.rget_with_confmod("a", p)[1] == 1

    def test_onimport(self, basedir):
        l = []
        conftest = Conftest(onimport=l.append)
        adir = basedir.join("adir")
        conftest_setinitial(conftest, [adir], confcutdir=basedir)
        assert len(l) == 1
        assert conftest.rget_with_confmod("a", adir)[1] == 1
        assert conftest.rget_with_confmod("b", adir.join("b"))[1] == 2
        assert len(l) == 2

    def test_immediate_initialiation_and_incremental_are_the_same(self, basedir):
        conftest = Conftest()
        len(conftest._path2confmods)
        conftest.getconftestmodules(basedir)
        snap1 = len(conftest._path2confmods)
        #assert len(conftest._path2confmods) == snap1 + 1
        conftest.getconftestmodules(basedir.join('adir'))
        assert len(conftest._path2confmods) == snap1 + 1
        conftest.getconftestmodules(basedir.join('b'))
        assert len(conftest._path2confmods) == snap1 + 2

    def test_value_access_not_existing(self, basedir):
        conftest = ConftestWithSetinitial(basedir)
        with pytest.raises(KeyError):
            conftest.rget_with_confmod('a', basedir)

    def test_value_access_by_path(self, basedir):
        conftest = ConftestWithSetinitial(basedir)
        adir = basedir.join("adir")
        assert conftest.rget_with_confmod("a", adir)[1] == 1
        assert conftest.rget_with_confmod("a", adir.join("b"))[1] == 1.5

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
    ConftestWithSetinitial(tmpdir.join("adir-1.0", "b"))

def test_doubledash_considered(testdir):
    conf = testdir.mkdir("--option")
    conf.join("conftest.py").ensure()
    conftest = Conftest()
    conftest_setinitial(conftest, [conf.basename, conf.basename])
    l = conftest.getconftestmodules(conf)
    assert len(l) == 1

def test_issue151_load_all_conftests(testdir):
    names = "code proj src".split()
    for name in names:
        p = testdir.mkdir(name)
        p.ensure("conftest.py")

    conftest = Conftest()
    conftest_setinitial(conftest, names)
    d = list(conftest._conftestpath2mod.values())
    assert len(d) == len(names)

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
    conftest = Conftest()
    conftest_setinitial(conftest, [testdir.tmpdir], confcutdir=p)
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
    conftest = Conftest()
    conftest_setinitial(conftest, [conf.dirpath()], confcutdir=conf.dirpath())
    l = conftest.getconftestmodules(conf.dirpath())
    assert len(l) == 1
    assert l[0].__file__.startswith(str(conf))

@pytest.mark.parametrize("name", 'test tests whatever .dotdir'.split())
def test_setinitial_conftest_subdirs(testdir, name):
    sub = testdir.mkdir(name)
    subconftest = sub.ensure("conftest.py")
    conftest = Conftest()
    conftest_setinitial(conftest, [sub.dirpath()], confcutdir=testdir.tmpdir)
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

def test_conftest_existing_resultlog(testdir):
    x = testdir.mkdir("tests")
    x.join("conftest.py").write(py.code.Source("""
        def pytest_addoption(parser):
            parser.addoption("--xyz", action="store_true")
    """))
    testdir.makefile(ext=".log", result="")  # Writes result.log
    result = testdir.runpytest("-h", "--resultlog", "result.log")
    result.stdout.fnmatch_lines(["*--xyz*"])

def test_conftest_existing_junitxml(testdir):
    x = testdir.mkdir("tests")
    x.join("conftest.py").write(py.code.Source("""
        def pytest_addoption(parser):
            parser.addoption("--xyz", action="store_true")
    """))
    testdir.makefile(ext=".xml", junit="")  # Writes junit.xml
    result = testdir.runpytest("-h", "--junitxml", "junit.xml")
    result.stdout.fnmatch_lines(["*--xyz*"])

def test_conftest_import_order(testdir, monkeypatch):
    ct1 = testdir.makeconftest("")
    sub = testdir.mkdir("sub")
    ct2 = sub.join("conftest.py")
    ct2.write("")
    def impct(p):
        return p
    conftest = Conftest()
    monkeypatch.setattr(conftest, 'importconftest', impct)
    assert conftest.getconftestmodules(sub) == [ct1, ct2]


def test_fixture_dependency(testdir, monkeypatch):
    ct1 = testdir.makeconftest("")
    ct1 = testdir.makepyfile("__init__.py")
    ct1.write("")
    sub = testdir.mkdir("sub")
    sub.join("__init__.py").write("")
    sub.join("conftest.py").write(py.std.textwrap.dedent("""
        import pytest

        @pytest.fixture
        def not_needed():
            assert False, "Should not be called!"

        @pytest.fixture
        def foo():
            assert False, "Should not be called!"

        @pytest.fixture
        def bar(foo):
            return 'bar'
    """))
    subsub = sub.mkdir("subsub")
    subsub.join("__init__.py").write("")
    subsub.join("test_bar.py").write(py.std.textwrap.dedent("""
        import pytest

        @pytest.fixture
        def bar():
            return 'sub bar'

        def test_event_fixture(bar):
            assert bar == 'sub bar'
    """))
    result = testdir.runpytest("sub")
    result.stdout.fnmatch_lines(["*1 passed*"])


def test_conftest_found_with_double_dash(testdir):
    sub = testdir.mkdir("sub")
    sub.join("conftest.py").write(py.std.textwrap.dedent("""
        def pytest_addoption(parser):
            parser.addoption("--hello-world", action="store_true")
    """))
    p = sub.join("test_hello.py")
    p.write(py.std.textwrap.dedent("""
        import pytest
        def test_hello(found):
            assert found == 1
    """))
    result = testdir.runpytest(str(p) + "::test_hello", "-h")
    result.stdout.fnmatch_lines("""
        *--hello-world*
    """)


class TestConftestVisibility:
    def _setup_tree(self, testdir):  # for issue616
        # example mostly taken from:
        # https://mail.python.org/pipermail/pytest-dev/2014-September/002617.html
        runner = testdir.mkdir("empty")
        package = testdir.mkdir("package")

        package.join("conftest.py").write(dedent("""\
            import pytest
            @pytest.fixture
            def fxtr():
                return "from-package"
        """))
        package.join("test_pkgroot.py").write(dedent("""\
            def test_pkgroot(fxtr):
                assert fxtr == "from-package"
        """))

        swc = package.mkdir("swc")
        swc.join("__init__.py").ensure()
        swc.join("conftest.py").write(dedent("""\
            import pytest
            @pytest.fixture
            def fxtr():
                return "from-swc"
        """))
        swc.join("test_with_conftest.py").write(dedent("""\
            def test_with_conftest(fxtr):
                assert fxtr == "from-swc"

        """))

        snc = package.mkdir("snc")
        snc.join("__init__.py").ensure()
        snc.join("test_no_conftest.py").write(dedent("""\
            def test_no_conftest(fxtr):
                assert fxtr == "from-package"   # No local conftest.py, so should
                                                # use value from parent dir's

        """))
        print ("created directory structure:")
        for x in testdir.tmpdir.visit():
            print ("   " + x.relto(testdir.tmpdir))

        return {
            "runner": runner,
            "package": package,
            "swc": swc,
            "snc": snc}

    # N.B.: "swc" stands for "subdir with conftest.py"
    #       "snc" stands for "subdir no [i.e. without] conftest.py"
    @pytest.mark.parametrize("chdir,testarg,expect_ntests_passed", [
	# Effective target: package/..
        ("runner",  "..",               3),
        ("package", "..",               3),
        ("swc",     "../..",            3),
        ("snc",     "../..",            3),

	# Effective target: package
        ("runner",  "../package",       3),
        ("package", ".",                3),
        ("swc",     "..",               3),
        ("snc",     "..",               3),

	# Effective target: package/swc
        ("runner",  "../package/swc",   1),
        ("package", "./swc",            1),
        ("swc",     ".",                1),
        ("snc",     "../swc",           1),

	# Effective target: package/snc
        ("runner",  "../package/snc",   1),
        ("package", "./snc",            1),
        ("swc",     "../snc",           1),
        ("snc",     ".",                1),
    ])
    @pytest.mark.issue616
    def test_parsefactories_relative_node_ids(
            self, testdir, chdir,testarg, expect_ntests_passed):
        dirs = self._setup_tree(testdir)
        print("pytest run in cwd: %s" %(
              dirs[chdir].relto(testdir.tmpdir)))
        print("pytestarg        : %s" %(testarg))
        print("expected pass    : %s" %(expect_ntests_passed))
        with dirs[chdir].as_cwd():
            reprec = testdir.inline_run(testarg, "-q", "--traceconfig")
            reprec.assertoutcome(passed=expect_ntests_passed)
