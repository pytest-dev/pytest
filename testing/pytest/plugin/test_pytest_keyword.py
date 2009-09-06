import py
from py.__.test.plugin.pytest_keyword import Mark

def test_pytest_mark_api():
    mark = Mark()
    py.test.raises(TypeError, "mark(x=3)")

    def f(): pass
    mark.hello(f)
    assert f.hello

    mark.world(x=3, y=4)(f)
    assert f.world 
    assert f.world.x == 3
    assert f.world.y == 4

    py.test.raises(TypeError, "mark.some(x=3)(f=5)")

def test_mark_plugin(testdir):
    p = testdir.makepyfile("""
        import py
        pytest_plugins = "keyword" 
        @py.test.mark.hello
        def test_hello():
            assert hasattr(test_hello, 'hello')
    """)
    result = testdir.runpytest(p)
    assert result.stdout.fnmatch_lines(["*passed*"])
