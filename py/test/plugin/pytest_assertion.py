import py

def pytest_addoption(parser):
    group = parser.getgroup("debugconfig")
    group._addoption('--no-assert', action="store_true", default=False, 
        dest="noassert", 
        help="disable python assert expression reinterpretation."),

def pytest_configure(config):
    if not config.getvalue("noassert"):
        warn_about_missing_assertion()
        config._oldassertion = py.std.__builtin__.AssertionError 
        py.std.__builtin__.AssertionError = py.code._AssertionError 

def pytest_unconfigure(config):
    if hasattr(config, '_oldassertion'):
        py.std.__builtin__.AssertionError = config._oldassertion
        del config._oldassertion

def warn_about_missing_assertion():
    try:
        assert False
    except AssertionError:
        pass
    else:
        py.std.warnings.warn("Assertions are turned off!"
                             " (are you using python -O?)")

def test_functional(testdir):
    testdir.makepyfile("""
        def test_hello():
            x = 3
            assert x == 4
    """)
    result = testdir.runpytest()
    assert "3 == 4" in result.stdout.str() 
    result = testdir.runpytest("--no-assert")
    assert "3 == 4" not in result.stdout.str() 

def test_traceback_failure(testdir):
    p1 = testdir.makepyfile("""
        def g():
            return 2
        def f(x):
            assert x == g()
        def test_onefails():
            f(3)
    """)
    result = testdir.runpytest(p1)
    result.stdout.fnmatch_lines([
        "*test_traceback_failure.py F", 
        "====* FAILURES *====",
        "____*____", 
        "",
        "    def test_onefails():",
        ">       f(3)",
        "",
        "*test_*.py:6: ",
        "_ _ _ *",
        #"",
        "    def f(x):",
        ">       assert x == g()",
        "E       assert 3 == 2",
        "E        +  where 2 = g()",
        "",
        "*test_traceback_failure.py:4: AssertionError"
    ])

