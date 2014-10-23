import sys
import pytest

class TestPasting:

    @pytest.fixture
    def pastebinlist(self, monkeypatch, request):
        pastebinlist = []
        plugin = request.config.pluginmanager.getplugin('pastebin')
        monkeypatch.setattr(plugin, 'create_new_paste', pastebinlist.append)
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
        s = pastebinlist[0]
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
        reprec = testdir.inline_run(testpath, "--pastebin=all", '-v')
        assert reprec.countoutcomes() == [1,1,1]
        assert len(pastebinlist) == 1
        s = pastebinlist[0]
        for x in 'test_fail test_skip test_pass'.split():
            assert x in s


class TestPaste:

    @pytest.fixture
    def pastebin(self, request):
        return request.config.pluginmanager.getplugin('pastebin')

    @pytest.fixture
    def mocked_urlopen(self, monkeypatch):
        """
        monkeypatch the actual urlopen calls done by the internal plugin
        function that connects to bpaste service.
        """
        calls = []
        def mocked(url, data):
            calls.append((url, data))
            class DummyFile:
                def read(self):
                    # part of html of a normal response
                    return 'View <a href="/raw/3c0c6750bd">raw</a>.'
            return DummyFile()

        if sys.version_info < (3, 0):
            import urllib
            monkeypatch.setattr(urllib, 'urlopen', mocked)
        else:
            import urllib.request
            monkeypatch.setattr(urllib.request, 'urlopen', mocked)
        return calls

    def test_create_new_paste(self, pastebin, mocked_urlopen):
        result = pastebin.create_new_paste('full-paste-contents')
        assert result == 'https://bpaste.net/show/3c0c6750bd'
        assert len(mocked_urlopen) == 1
        url, data = mocked_urlopen[0]
        lexer = 'python3' if sys.version_info[0] == 3 else 'python'
        assert url == 'https://bpaste.net'
        assert 'lexer=%s' % lexer in data
        assert 'code=full-paste-contents' in data
        assert 'expiry=1week' in data


