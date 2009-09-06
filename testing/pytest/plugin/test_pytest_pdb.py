import py

class TestPDB: 
    def pytest_funcarg__pdblist(self, request):
        monkeypatch = request.getfuncargvalue("monkeypatch")
        pdblist = []
        def mypdb(*args):
            pdblist.append(args)
        plugin = request.config.pluginmanager.impname2plugin['pytest_pdb']
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
        #child.expect(".*def test_1.*")
        child.expect(".*i = 0.*")
        child.expect("(Pdb)")
        child.sendeof()
        child.expect("1 failed")
        if child.isalive(): 
            child.wait()

    def test_incompatibility_messages(self, testdir):
        Error = py.test.config.Error
        py.test.raises(Error, "testdir.parseconfigure('--pdb', '--looponfail')")
        result = testdir.runpytest("--pdb", "-n", "3")
        assert result.ret != 0
        assert "incompatible" in result.stdout.str()
        result = testdir.runpytest("--pdb", "-d", "--tx", "popen")
        assert result.ret != 0
        assert "incompatible" in result.stdout.str()
