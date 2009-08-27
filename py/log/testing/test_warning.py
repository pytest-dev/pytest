import py
mypath = py.path.local(__file__).new(ext=".py")

def test_forwarding_to_warnings_module():
    py.test.deprecated_call(py.log._apiwarn, "1.3", "..")

def test_apiwarn_functional():
    capture = py.io.StdCapture()
    py.log._apiwarn("x.y.z", "something")
    out, err = capture.reset()
    print "out", out
    print "err", err
    assert err.find("x.y.z") != -1
    lno = test_apiwarn_functional.func_code.co_firstlineno + 2
    exp = "%s:%s" % (mypath, lno)
    assert err.find(exp) != -1

def test_stacklevel():
    def f():
        py.log._apiwarn("x", "some", stacklevel=2)
    # 3
    # 4
    capture = py.io.StdCapture()
    f()
    out, err = capture.reset()
    lno = test_stacklevel.func_code.co_firstlineno + 6
    warning = str(err)
    assert warning.find(":%s" % lno) != -1

def test_stacklevel_initpkg_with_resolve(testdir):
    mod = testdir.makepyfile(initpkg="""
        import py
        def __getattr__():
            f()
        def f():
            py.log._apiwarn("x", "some", stacklevel="initpkg")
    """).pyimport()
    capture = py.io.StdCapture()
    mod.__getattr__()
    out, err = capture.reset()
    lno = test_stacklevel_initpkg_with_resolve.func_code.co_firstlineno + 9
    warning = str(err)
    assert warning.find(":%s" % lno) != -1

def test_stacklevel_initpkg_no_resolve():
    def f():
        py.log._apiwarn("x", "some", stacklevel="initpkg")
    capture = py.io.StdCapture()
    f()
    out, err = capture.reset()
    lno = test_stacklevel_initpkg_no_resolve.func_code.co_firstlineno + 2
    warning = str(err)
    assert warning.find(":%s" % lno) != -1


def test_function():
    capture = py.io.StdCapture()
    py.log._apiwarn("x.y.z", "something", function=test_function)
    out, err = capture.reset()
    print "out", out
    print "err", err
    assert err.find("x.y.z") != -1
    lno = test_function.func_code.co_firstlineno 
    exp = "%s:%s" % (mypath, lno)
    assert err.find(exp) != -1

