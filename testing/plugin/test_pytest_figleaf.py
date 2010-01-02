import py

def test_functional(testdir):
    py.test.importorskip("figleaf")
    testdir.makepyfile("""
        def f():    
            x = 42
        def test_whatever():
            pass
        """)
    result = testdir.runpytest('--figleaf')
    assert result.ret == 0
    assert result.stdout.fnmatch_lines([
        '*figleaf html*'
        ])
    #print result.stdout.str()

