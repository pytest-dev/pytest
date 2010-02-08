import py

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

    def test_pdb_on_skip(self, testdir, pdblist):
        rep = testdir.inline_runsource1('--pdb', """
            import py
            def test_func():
                py.test.skip("hello")
        """)
        assert rep.skipped 
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
        child.expect("1 failed")
        if child.isalive(): 
            child.wait()

    def test_pdb_interaction_exception(self, testdir):
        p1 = testdir.makepyfile("""
            import py
            def globalfunc():
                pass
            def test_1():
                py.test.raises(ValueError, globalfunc)
        """)
        child = testdir.spawn_pytest("--pdb %s" % p1)
        child.expect(".*def test_1")
        child.expect(".*py.test.raises.*globalfunc")
        child.expect("(Pdb)")
        child.sendline("globalfunc")
        child.expect(".*function")
        child.sendeof()
        child.expect("1 failed")
        if child.isalive(): 
            child.wait()
