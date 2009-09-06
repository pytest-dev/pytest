import py

def test_functional(testdir):
    py.test.importorskip("figleaf")
    testdir.plugins.append("figleaf")
    testdir.makepyfile("""
        def f():    
            x = 42
        def test_whatever():
            pass
        """)
    result = testdir.runpytest('-F')
    assert result.ret == 0
    assert result.stdout.fnmatch_lines([
        '*figleaf html*'
        ])
    #print result.stdout.str()
