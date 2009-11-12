
def test_functional_deprecation(testdir):
    testdir.makepyfile("""
        import py
        def test_compat_deprecations(recwarn):
            for name in 'subprocess optparse textwrap doctest'.split():
                check(recwarn, name)
        def check(recwarn, name):
            x = getattr(py.compat, name)
            warn = recwarn.pop(DeprecationWarning)
            recwarn.clear()
            assert x == getattr(py.std, name)
            assert warn.filename.find("test_functional_deprecation.py") != -1
    """)
    result = testdir.runpytest()
    assert result.ret == 0


