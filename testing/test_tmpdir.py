import py, pytest
import os

from _pytest.tmpdir import tmpdir, TempdirHandler

def test_funcarg(testdir):
    testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall(id='a')
                metafunc.addcall(id='b')
            def test_func(tmpdir): pass
    """)
    reprec = testdir.inline_run()
    calls = reprec.getcalls("pytest_runtest_setup")
    item = calls[0].item
    # pytest_unconfigure has deleted the TempdirHandler already
    config = item.config
    config._tmpdirhandler = TempdirHandler(config)
    p = tmpdir(item._request)
    assert p.check()
    bn = p.basename.strip("0123456789")
    assert bn.endswith("test_func_a_")
    item.name = "qwe/\\abc"
    p = tmpdir(item._request)
    assert p.check()
    bn = p.basename.strip("0123456789")
    assert bn == "qwe__abc"

def test_ensuretemp(recwarn):
    #py.test.deprecated_call(py.test.ensuretemp, 'hello')
    d1 = py.test.ensuretemp('hello')
    d2 = py.test.ensuretemp('hello')
    assert d1 == d2
    assert d1.check(dir=1)

class TestTempdirHandler:
    def test_mktemp(self, testdir):
        config = testdir.Config()
        config.option.basetemp = testdir.mkdir("hello")
        t = TempdirHandler(config)
        tmp = t.mktemp("world")
        assert tmp.relto(t.getbasetemp()) == "world0"
        tmp = t.mktemp("this")
        assert tmp.relto(t.getbasetemp()).startswith("this")
        tmp2 = t.mktemp("this")
        assert tmp2.relto(t.getbasetemp()).startswith("this")
        assert tmp2 != tmp

class TestConfigTmpdir:
    def test_getbasetemp_custom_removes_old(self, testdir):
        p = testdir.tmpdir.join("xyz")
        config = testdir.parseconfigure("--basetemp=xyz")
        b = config._tmpdirhandler.getbasetemp()
        assert b == p
        h = b.ensure("hello")
        config._tmpdirhandler.getbasetemp()
        assert h.check()
        config = testdir.parseconfigure("--basetemp=xyz")
        b2 = config._tmpdirhandler.getbasetemp()
        assert b2.check()
        assert not h.check()

def test_basetemp(testdir):
    mytemp = testdir.tmpdir.mkdir("mytemp")
    p = testdir.makepyfile("""
        import pytest
        def test_1():
            pytest.ensuretemp("hello")
    """)
    result = testdir.runpytest(p, '--basetemp=%s' % mytemp)
    assert result.ret == 0
    assert mytemp.join('hello').check()

@pytest.mark.skipif("not hasattr(py.path.local, 'mksymlinkto')")
def test_tmpdir_always_is_realpath(testdir):
    # the reason why tmpdir should be a realpath is that
    # when you cd to it and do "os.getcwd()" you will anyway
    # get the realpath.  Using the symlinked path can thus
    # easily result in path-inequality
    # XXX if that proves to be a problem, consider using
    # os.environ["PWD"]
    realtemp = testdir.tmpdir.mkdir("myrealtemp")
    linktemp = testdir.tmpdir.join("symlinktemp")
    linktemp.mksymlinkto(realtemp)
    p = testdir.makepyfile("""
        def test_1(tmpdir):
            import os
            assert os.path.realpath(str(tmpdir)) == str(tmpdir)
    """)
    result = testdir.runpytest("-s", p, '--basetemp=%s/bt' % linktemp)
    assert not result.ret

