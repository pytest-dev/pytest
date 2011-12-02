import pytest, py, os, sys
from _pytest.capture import CaptureManager

needsosdup = pytest.mark.xfail("not hasattr(os, 'dup')")

class TestCaptureManager:
    def test_getmethod_default_no_fd(self, testdir, monkeypatch):
        config = testdir.parseconfig(testdir.tmpdir)
        assert config.getvalue("capture") is None
        capman = CaptureManager()
        monkeypatch.delattr(os, 'dup', raising=False)
        try:
            assert capman._getmethod(config, None) == "sys"
        finally:
            monkeypatch.undo()

    def test_configure_per_fspath(self, testdir):
        config = testdir.parseconfig(testdir.tmpdir)
        capman = CaptureManager()
        hasfd = hasattr(os, 'dup')
        if hasfd:
            assert capman._getmethod(config, None) == "fd"
        else:
            assert capman._getmethod(config, None) == "sys"

        for name in ('no', 'fd', 'sys'):
            if not hasfd and name == 'fd':
                continue
            sub = testdir.tmpdir.mkdir("dir" + name)
            sub.ensure("__init__.py")
            sub.join("conftest.py").write('option_capture = %r' % name)
            assert capman._getmethod(config, sub.join("test_hello.py")) == name

    @needsosdup
    @pytest.mark.multi(method=['no', 'fd', 'sys'])
    def test_capturing_basic_api(self, method):
        capouter = py.io.StdCaptureFD()
        old = sys.stdout, sys.stderr, sys.stdin
        try:
            capman = CaptureManager()
            # call suspend without resume or start
            outerr = capman.suspendcapture()
            outerr = capman.suspendcapture()
            assert outerr == ("", "")
            capman.resumecapture(method)
            print ("hello")
            out, err = capman.suspendcapture()
            if method == "no":
                assert old == (sys.stdout, sys.stderr, sys.stdin)
            else:
                assert out == "hello\n"
            capman.resumecapture(method)
            out, err = capman.suspendcapture()
            assert not out and not err
            capman.reset_capturings()
        finally:
            capouter.reset()

    @needsosdup
    def test_juggle_capturings(self, testdir):
        capouter = py.io.StdCaptureFD()
        try:
            #config = testdir.parseconfig(testdir.tmpdir)
            capman = CaptureManager()
            try:
                capman.resumecapture("fd")
                pytest.raises(ValueError, 'capman.resumecapture("fd")')
                pytest.raises(ValueError, 'capman.resumecapture("sys")')
                os.write(1, "hello\n".encode('ascii'))
                out, err = capman.suspendcapture()
                assert out == "hello\n"
                capman.resumecapture("sys")
                os.write(1, "hello\n".encode('ascii'))
                py.builtin.print_("world", file=sys.stderr)
                out, err = capman.suspendcapture()
                assert not out
                assert err == "world\n"
            finally:
                capman.reset_capturings()
        finally:
            capouter.reset()

@pytest.mark.xfail("hasattr(sys, 'pypy_version_info')")
@pytest.mark.multi(method=['fd', 'sys'])
def test_capturing_unicode(testdir, method):
    if sys.version_info >= (3,0):
        obj = "'b\u00f6y'"
    else:
        obj = "u'\u00f6y'"
    testdir.makepyfile("""
        # coding=utf8
        # taken from issue 227 from nosetests
        def test_unicode():
            import sys
            print (sys.stdout)
            print (%s)
    """ % obj)
    result = testdir.runpytest("--capture=%s" % method)
    result.stdout.fnmatch_lines([
        "*1 passed*"
    ])

@pytest.mark.multi(method=['fd', 'sys'])
def test_capturing_bytes_in_utf8_encoding(testdir, method):
    testdir.makepyfile("""
        def test_unicode():
            print ('b\\u00f6y')
    """)
    result = testdir.runpytest("--capture=%s" % method)
    result.stdout.fnmatch_lines([
        "*1 passed*"
    ])

def test_collect_capturing(testdir):
    p = testdir.makepyfile("""
        print ("collect %s failure" % 13)
        import xyz42123
    """)
    result = testdir.runpytest(p)
    result.stdout.fnmatch_lines([
        "*Captured stdout*",
        "*collect 13 failure*",
    ])

class TestPerTestCapturing:
    def test_capture_and_fixtures(self, testdir):
        p = testdir.makepyfile("""
            def setup_module(mod):
                print ("setup module")
            def setup_function(function):
                print ("setup " + function.__name__)
            def test_func1():
                print ("in func1")
                assert 0
            def test_func2():
                print ("in func2")
                assert 0
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "setup module*",
            "setup test_func1*",
            "in func1*",
            "setup test_func2*",
            "in func2*",
        ])

    @pytest.mark.xfail
    def test_capture_scope_cache(self, testdir):
        p = testdir.makepyfile("""
            import sys
            def setup_module(func):
                print ("module-setup")
            def setup_function(func):
                print ("function-setup")
            def test_func():
                print ("in function")
                assert 0
            def teardown_function(func):
                print ("in teardown")
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*test_func():*",
            "*Captured stdout during setup*",
            "module-setup*",
            "function-setup*",
            "*Captured stdout*",
            "in teardown*",
        ])


    def test_no_carry_over(self, testdir):
        p = testdir.makepyfile("""
            def test_func1():
                print ("in func1")
            def test_func2():
                print ("in func2")
                assert 0
        """)
        result = testdir.runpytest(p)
        s = result.stdout.str()
        assert "in func1" not in s
        assert "in func2" in s


    def test_teardown_capturing(self, testdir):
        p = testdir.makepyfile("""
            def setup_function(function):
                print ("setup func1")
            def teardown_function(function):
                print ("teardown func1")
                assert 0
            def test_func1():
                print ("in func1")
                pass
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            '*teardown_function*',
            '*Captured stdout*',
            "setup func1*",
            "in func1*",
            "teardown func1*",
            #"*1 fixture failure*"
        ])

    def test_teardown_capturing_final(self, testdir):
        p = testdir.makepyfile("""
            def teardown_module(mod):
                print ("teardown module")
                assert 0
            def test_func():
                pass
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*def teardown_module(mod):*",
            "*Captured stdout*",
            "*teardown module*",
            "*1 error*",
        ])

    def test_capturing_outerr(self, testdir):
        p1 = testdir.makepyfile("""
            import sys
            def test_capturing():
                print (42)
                sys.stderr.write(str(23))
            def test_capturing_error():
                print (1)
                sys.stderr.write(str(2))
                raise ValueError
        """)
        result = testdir.runpytest(p1)
        result.stdout.fnmatch_lines([
            "*test_capturing_outerr.py .F",
            "====* FAILURES *====",
            "____*____",
            "*test_capturing_outerr.py:8: ValueError",
            "*--- Captured stdout ---*",
            "1",
            "*--- Captured stderr ---*",
            "2",
        ])

class TestLoggingInteraction:
    def test_logging_stream_ownership(self, testdir):
        p = testdir.makepyfile("""
            def test_logging():
                import logging
                import pytest
                stream = py.io.TextIO()
                logging.basicConfig(stream=stream)
                stream.close() # to free memory/release resources
        """)
        result = testdir.runpytest(p)
        result.stderr.str().find("atexit") == -1

    def test_logging_and_immediate_setupteardown(self, testdir):
        p = testdir.makepyfile("""
            import logging
            def setup_function(function):
                logging.warn("hello1")

            def test_logging():
                logging.warn("hello2")
                assert 0

            def teardown_function(function):
                logging.warn("hello3")
                assert 0
        """)
        for optargs in (('--capture=sys',), ('--capture=fd',)):
            print (optargs)
            result = testdir.runpytest(p, *optargs)
            s = result.stdout.str()
            result.stdout.fnmatch_lines([
                "*WARN*hello3",  # errors show first!
                "*WARN*hello1",
                "*WARN*hello2",
            ])
            # verify proper termination
            assert "closed" not in s

    def test_logging_and_crossscope_fixtures(self, testdir):
        p = testdir.makepyfile("""
            import logging
            def setup_module(function):
                logging.warn("hello1")

            def test_logging():
                logging.warn("hello2")
                assert 0

            def teardown_module(function):
                logging.warn("hello3")
                assert 0
        """)
        for optargs in (('--capture=sys',), ('--capture=fd',)):
            print (optargs)
            result = testdir.runpytest(p, *optargs)
            s = result.stdout.str()
            result.stdout.fnmatch_lines([
                "*WARN*hello3",  # errors come first
                "*WARN*hello1",
                "*WARN*hello2",
            ])
            # verify proper termination
            assert "closed" not in s

    def test_logging_initialized_in_test(self, testdir):
        p = testdir.makepyfile("""
            import sys
            def test_something():
                # pytest does not import logging
                assert 'logging' not in sys.modules
                import logging
                logging.basicConfig()
                logging.warn("hello432")
                assert 0
        """)
        result = testdir.runpytest(p, "--traceconfig",
            "-p", "no:capturelog")
        assert result.ret != 0
        result.stdout.fnmatch_lines([
            "*hello432*",
        ])
        assert 'operation on closed file' not in result.stderr.str()

    def test_conftestlogging_is_shown(self, testdir):
        testdir.makeconftest("""
                import logging
                logging.basicConfig()
                logging.warn("hello435")
        """)
        # make sure that logging is still captured in tests
        result = testdir.runpytest("-s", "-p", "no:capturelog")
        assert result.ret == 0
        result.stderr.fnmatch_lines([
            "WARNING*hello435*",
        ])
        assert 'operation on closed file' not in result.stderr.str()

    def test_conftestlogging_and_test_logging(self, testdir):
        testdir.makeconftest("""
                import logging
                logging.basicConfig()
        """)
        # make sure that logging is still captured in tests
        p = testdir.makepyfile("""
            def test_hello():
                import logging
                logging.warn("hello433")
                assert 0
        """)
        result = testdir.runpytest(p, "-p", "no:capturelog")
        assert result.ret != 0
        result.stdout.fnmatch_lines([
            "WARNING*hello433*",
        ])
        assert 'something' not in result.stderr.str()
        assert 'operation on closed file' not in result.stderr.str()


class TestCaptureFuncarg:
    def test_std_functional(self, testdir):
        reprec = testdir.inline_runsource("""
            def test_hello(capsys):
                print (42)
                out, err = capsys.readouterr()
                assert out.startswith("42")
        """)
        reprec.assertoutcome(passed=1)

    @needsosdup
    def test_stdfd_functional(self, testdir):
        reprec = testdir.inline_runsource("""
            def test_hello(capfd):
                import os
                os.write(1, "42".encode('ascii'))
                out, err = capfd.readouterr()
                assert out.startswith("42")
                capfd.close()
        """)
        reprec.assertoutcome(passed=1)

    def test_partial_setup_failure(self, testdir):
        p = testdir.makepyfile("""
            def test_hello(capsys, missingarg):
                pass
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*test_partial_setup_failure*",
            "*1 error*",
        ])

    @needsosdup
    def test_keyboardinterrupt_disables_capturing(self, testdir):
        p = testdir.makepyfile("""
            def test_hello(capfd):
                import os
                os.write(1, str(42).encode('ascii'))
                raise KeyboardInterrupt()
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            "*KeyboardInterrupt*"
        ])
        assert result.ret == 2

def test_setup_failure_does_not_kill_capturing(testdir):
    sub1 = testdir.mkpydir("sub1")
    sub1.join("conftest.py").write(py.code.Source("""
        def pytest_runtest_setup(item):
            raise ValueError(42)
    """))
    sub1.join("test_mod.py").write("def test_func1(): pass")
    result = testdir.runpytest(testdir.tmpdir, '--traceconfig')
    result.stdout.fnmatch_lines([
        "*ValueError(42)*",
        "*1 error*"
    ])

def test_fdfuncarg_skips_on_no_osdup(testdir):
    testdir.makepyfile("""
        import os
        if hasattr(os, 'dup'):
            del os.dup
        def test_hello(capfd):
            pass
    """)
    result = testdir.runpytest("--capture=no")
    result.stdout.fnmatch_lines([
        "*1 skipped*"
    ])

def test_capture_conftest_runtest_setup(testdir):
    testdir.makeconftest("""
        def pytest_runtest_setup():
            print ("hello19")
    """)
    testdir.makepyfile("def test_func(): pass")
    result = testdir.runpytest()
    assert result.ret == 0
    assert 'hello19' not in result.stdout.str()
