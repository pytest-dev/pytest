import pytest

class TestPasting:
    def pytest_funcarg__pastebinlist(self, request):
        mp = request.getfuncargvalue("monkeypatch")
        pastebinlist = []
        class MockProxy:
            def newPaste(self, language, code):
                pastebinlist.append((language, code))
        plugin = request.config.pluginmanager.getplugin('pastebin')
        mp.setattr(plugin, 'getproxy', MockProxy)
        return pastebinlist

    def test_failed(self, testdir, pastebinlist):
        testpath = testdir.makepyfile("""
            import pytest
            def test_pass():
                pass
            def test_fail():
                assert 0
            def test_skip():
                pytest.skip("")
        """)
        reprec = testdir.inline_run(testpath, "--paste=failed")
        assert len(pastebinlist) == 1
        assert pastebinlist[0][0] == "python"
        s = pastebinlist[0][1]
        assert s.find("def test_fail") != -1
        assert reprec.countoutcomes() == [1,1,1]

    def test_all(self, testdir, pastebinlist):
        testpath = testdir.makepyfile("""
            import pytest
            def test_pass():
                pass
            def test_fail():
                assert 0
            def test_skip():
                pytest.skip("")
        """)
        reprec = testdir.inline_run(testpath, "--pastebin=all")
        assert reprec.countoutcomes() == [1,1,1]
        assert len(pastebinlist) == 1
        assert pastebinlist[0][0] == "python"
        s = pastebinlist[0][1]
        for x in 'test_fail test_skip skipped'.split():
            assert s.find(x), (s, x)


class TestRPCClient:
    def pytest_funcarg__pastebin(self, request):
        return request.config.pluginmanager.getplugin('pastebin')

    def test_getproxy(self, pastebin):
        proxy = pastebin.getproxy()
        assert proxy is not None
        assert proxy.__class__.__module__.startswith('xmlrpc')

    
