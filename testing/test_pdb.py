import py, pytest
import sys

class TestPDB:
    def pytest_funcarg__pdblist(self, request):
        monkeypatch = request.getfuncargvalue("monkeypatch")
        pdblist = []
        def mypdb(*args):
            pdblist.append(args)
        plugin = request.config.pluginmanager.getplugin('pdb')
        monkeypatch.setattr(plugin, 'post_mortem', mypdb)
        return pdblist

    def test_pdb_on_fail(self, testdir, pdblist):
        rep = testdir.inline_runsource1('--pdb', """
            def test_func():
                assert 0
        """)
        assert rep.failed
        assert len(pdblist) == 1
        tb = py.code.Traceback(pdblist[0][0])
        assert tb[-1].name == "test_func"

    def test_pdb_on_xfail(self, testdir, pdblist):
        rep = testdir.inline_runsource1('--pdb', """
            import pytest
            @pytest.mark.xfail
            def test_func():
                assert 0
        """)
        assert "xfail" in rep.keywords
        assert not pdblist

    def test_pdb_on_skip(self, testdir, pdblist):
        rep = testdir.inline_runsource1('--pdb', """
            import pytest
            def test_func():
                pytest.skip("hello")
        """)
        assert rep.skipped
        assert len(pdblist) == 0

    def test_pdb_on_BdbQuit(self, testdir, pdblist):
        rep = testdir.inline_runsource1('--pdb', """
            import bdb
            def test_func():
                raise bdb.BdbQuit
        """)
        assert rep.failed
        assert len(pdblist) == 0

    def test_pdb_interaction(self, testdir):
        p1 = testdir.makepyfile("""
            def test_1():
                i = 0
                assert i == 1
        """)
        child = testdir.spawn_pytest("--pdb %s" % p1)
        child.expect(".*def test_1")
        child.expect(".*i = 0")
        child.expect("(Pdb)")
        child.sendeof()
        rest = child.read()
        assert "1 failed" in rest
        assert "def test_1" not in rest
        if child.isalive():
            child.wait()

    def test_pdb_interaction_exception(self, testdir):
        p1 = testdir.makepyfile("""
            import pytest
            def globalfunc():
                pass
            def test_1():
                pytest.raises(ValueError, globalfunc)
        """)
        child = testdir.spawn_pytest("--pdb %s" % p1)
        child.expect(".*def test_1")
        child.expect(".*pytest.raises.*globalfunc")
        child.expect("(Pdb)")
        child.sendline("globalfunc")
        child.expect(".*function")
        child.sendeof()
        child.expect("1 failed")
        if child.isalive():
            child.wait()

    def test_pdb_interaction_capturing_simple(self, testdir):
        p1 = testdir.makepyfile("""
            import pytest
            def test_1():
                i = 0
                print ("hello17")
                pytest.set_trace()
                x = 3
        """)
        child = testdir.spawn_pytest(str(p1))
        child.expect("test_1")
        child.expect("x = 3")
        child.expect("(Pdb)")
        child.sendeof()
        rest = child.read()
        assert "1 failed" in rest
        assert "def test_1" in rest
        assert "hello17" in rest # out is captured
        if child.isalive():
            child.wait()

    def test_pdb_interaction_doctest(self, testdir):
        p1 = testdir.makepyfile("""
            import pytest
            def function_1():
                '''
                >>> i = 0
                >>> assert i == 1
                '''
        """)
        child = testdir.spawn_pytest("--doctest-modules --pdb %s" % p1)
        child.expect("(Pdb)")
        child.sendline('i')
        child.expect("0")
        child.expect("(Pdb)")
        child.sendeof()
        rest = child.read()
        assert "1 failed" in rest
        if child.isalive():
            child.wait()

    def test_pdb_interaction_capturing_twice(self, testdir):
        p1 = testdir.makepyfile("""
            import pytest
            def test_1():
                i = 0
                print ("hello17")
                pytest.set_trace()
                x = 3
                print ("hello18")
                pytest.set_trace()
                x = 4
        """)
        child = testdir.spawn_pytest(str(p1))
        child.expect("test_1")
        child.expect("x = 3")
        child.expect("(Pdb)")
        child.sendline('c')
        child.expect("x = 4")
        child.sendeof()
        rest = child.read()
        assert "1 failed" in rest
        assert "def test_1" in rest
        assert "hello17" in rest # out is captured
        assert "hello18" in rest # out is captured
        if child.isalive():
            child.wait()

    def test_pdb_used_outside_test(self, testdir):
        p1 = testdir.makepyfile("""
            import pytest
            pytest.set_trace()
            x = 5
        """)
        child = testdir.spawn("%s %s" %(sys.executable, p1))
        child.expect("x = 5")
        child.sendeof()
        child.wait()

    def test_pdb_used_in_generate_tests(self, testdir):
        p1 = testdir.makepyfile("""
            import pytest
            def pytest_generate_tests(metafunc):
                pytest.set_trace()
                x = 5
            def test_foo(a):
                pass
        """)
        child = testdir.spawn_pytest(str(p1))
        child.expect("x = 5")
        child.sendeof()
        child.wait()
    def test_pdb_collection_failure_is_shown(self, testdir):
        p1 = testdir.makepyfile("""xxx """)
        result = testdir.runpytest("--pdb", p1)
        result.stdout.fnmatch_lines([
            "*NameError*xxx*",
            "*1 error*",
        ])
