import os
import pytest
import shutil
import py

pytest_plugins = "pytester",


class TestLastFailed:
    @pytest.mark.skipif("sys.version_info < (2,6)")
    def test_lastfailed_usecase(self, testdir, monkeypatch):
        monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", 1)
        p = testdir.makepyfile("""
            def test_1():
                assert 0
            def test_2():
                assert 0
            def test_3():
                assert 1
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*2 failed*",
        ])
        p.write(py.code.Source("""
            def test_1():
                assert 1

            def test_2():
                assert 1

            def test_3():
                assert 0
        """))
        result = testdir.runpytest("--lf")
        result.stdout.fnmatch_lines([
            "*2 passed*1 desel*",
        ])
        result = testdir.runpytest("--lf")
        result.stdout.fnmatch_lines([
            "*1 failed*2 passed*",
        ])
        result = testdir.runpytest("--lf", "--clearcache")
        result.stdout.fnmatch_lines([
            "*1 failed*2 passed*",
        ])

        # Run this again to make sure clearcache is robust
        if os.path.isdir('.cache'):
            shutil.rmtree('.cache')
        result = testdir.runpytest("--lf", "--clearcache")
        result.stdout.fnmatch_lines([
            "*1 failed*2 passed*",
        ])

    def test_failedfirst_order(self, testdir):
        always_pass = testdir.tmpdir.join('test_a.py').write(py.code.Source("""
            def test_always_passes():
                assert 1
        """))
        always_fail = testdir.tmpdir.join('test_b.py').write(py.code.Source("""
            def test_always_fails():
                assert 0
        """))
        result = testdir.runpytest()
        # Test order will be collection order; alphabetical
        result.stdout.fnmatch_lines([
            "test_a.py*",
            "test_b.py*",
        ])
        result = testdir.runpytest("--lf", "--ff")
        # Test order will be failing tests firs
        result.stdout.fnmatch_lines([
            "test_b.py*",
            "test_a.py*",
        ])

    @pytest.mark.skipif("sys.version_info < (2,6)")
    def test_lastfailed_difference_invocations(self, testdir, monkeypatch):
        monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", 1)
        testdir.makepyfile(test_a="""
            def test_a1():
                assert 0
            def test_a2():
                assert 1
        """, test_b="""
            def test_b1():
                assert 0
        """)
        p = testdir.tmpdir.join("test_a.py")
        p2 = testdir.tmpdir.join("test_b.py")

        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*2 failed*",
        ])
        result = testdir.runpytest("--lf", p2)
        result.stdout.fnmatch_lines([
            "*1 failed*",
        ])
        p2.write(py.code.Source("""
            def test_b1():
                assert 1
        """))
        result = testdir.runpytest("--lf", p2)
        result.stdout.fnmatch_lines([
            "*1 passed*",
        ])
        result = testdir.runpytest("--lf", p)
        result.stdout.fnmatch_lines([
            "*1 failed*1 desel*",
        ])

    @pytest.mark.skipif("sys.version_info < (2,6)")
    def test_lastfailed_usecase_splice(self, testdir, monkeypatch):
        monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", 1)
        p1 = testdir.makepyfile("""
            def test_1():
                assert 0
        """)
        p2 = testdir.tmpdir.join("test_something.py")
        p2.write(py.code.Source("""
            def test_2():
                assert 0
        """))
        result = testdir.runpytest()
        result.stdout.fnmatch_lines([
            "*2 failed*",
        ])
        result = testdir.runpytest("--lf", p2)
        result.stdout.fnmatch_lines([
            "*1 failed*",
        ])
        result = testdir.runpytest("--lf")
        result.stdout.fnmatch_lines([
            "*2 failed*",
        ])

    def test_lastfailed_xpass(self, testdir):
        rep = testdir.inline_runsource("""
            import pytest
            @pytest.mark.xfail
            def test_hello():
                assert 1
        """)
        config = testdir.parseconfigure()
        lastfailed = config.cache.get("cache/lastfailed", -1)
        assert not lastfailed

    def test_lastfailed_collectfailure(self, testdir, monkeypatch):

        testdir.makepyfile(test_maybe="""
            import py
            env = py.std.os.environ
            if '1' == env['FAILIMPORT']:
                raise ImportError('fail')
            def test_hello():
                assert '0' == env['FAILTEST']
        """)

        def rlf(fail_import, fail_run):
            monkeypatch.setenv('FAILIMPORT', fail_import)
            monkeypatch.setenv('FAILTEST', fail_run)

            testdir.runpytest('-q')
            config = testdir.parseconfigure()
            lastfailed = config.cache.get("cache/lastfailed", -1)
            return lastfailed

        lastfailed = rlf(fail_import=0, fail_run=0)
        assert not lastfailed

        lastfailed = rlf(fail_import=1, fail_run=0)
        assert list(lastfailed) == ['test_maybe.py']

        lastfailed = rlf(fail_import=0, fail_run=1)
        assert list(lastfailed) == ['test_maybe.py::test_hello']


    def test_lastfailed_failure_subset(self, testdir, monkeypatch):

        testdir.makepyfile(test_maybe="""
            import py
            env = py.std.os.environ
            if '1' == env['FAILIMPORT']:
                raise ImportError('fail')
            def test_hello():
                assert '0' == env['FAILTEST']
        """)

        testdir.makepyfile(test_maybe2="""
            import py
            env = py.std.os.environ
            if '1' == env['FAILIMPORT']:
                raise ImportError('fail')
            def test_hello():
                assert '0' == env['FAILTEST']

            def test_pass():
                pass
        """)

        def rlf(fail_import, fail_run, args=()):
            monkeypatch.setenv('FAILIMPORT', fail_import)
            monkeypatch.setenv('FAILTEST', fail_run)

            result = testdir.runpytest('-q', '--lf', *args)
            config = testdir.parseconfigure()
            lastfailed = config.cache.get("cache/lastfailed", -1)
            return result, lastfailed

        result, lastfailed = rlf(fail_import=0, fail_run=0)
        assert not lastfailed
        result.stdout.fnmatch_lines([
            '*3 passed*',
        ])

        result, lastfailed = rlf(fail_import=1, fail_run=0)
        assert sorted(list(lastfailed)) == ['test_maybe.py', 'test_maybe2.py']


        result, lastfailed = rlf(fail_import=0, fail_run=0,
                                 args=('test_maybe2.py',))
        assert list(lastfailed) == ['test_maybe.py']


        # edge case of test selection - even if we remember failures
        # from other tests we still need to run all tests if no test
        # matches the failures
        result, lastfailed = rlf(fail_import=0, fail_run=0,
                                 args=('test_maybe2.py',))
        assert list(lastfailed) == ['test_maybe.py']
        result.stdout.fnmatch_lines([
            '*2 passed*',
        ])
