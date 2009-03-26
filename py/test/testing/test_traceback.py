import py

class TestTracebackCutting:
    def test_skip_simple(self):
        from py.__.test.outcome import Skipped
        excinfo = py.test.raises(Skipped, 'py.test.skip("xxx")')
        assert excinfo.traceback[-1].frame.code.name == "skip"
        assert excinfo.traceback[-1].ishidden()

    def test_traceback_argsetup(self, testdir):
        testdir.makeconftest("""
            class ConftestPlugin:
                def pytest_funcarg__hello(self, pyfuncitem):
                    raise ValueError("xyz")
        """)
        p = testdir.makepyfile("def test(hello): pass")
        result = testdir.runpytest(p)
        assert result.ret != 0
        out = result.stdout.str()
        assert out.find("xyz") != -1
        assert out.find("conftest.py:3: ValueError") != -1
        numentries = out.count("_ _ _") # separator for traceback entries
        assert numentries == 0

        result = testdir.runpytest("--fulltrace", p)
        out = result.stdout.str()
        assert out.find("conftest.py:3: ValueError") != -1
        numentries = out.count("_ _ _ _") # separator for traceback entries
        assert numentries >3
