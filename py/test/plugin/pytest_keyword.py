"""
    py.test.mark / keyword plugin 
"""
import py

def pytest_namespace():
    mark = KeywordDecorator({})
    return {'mark': mark}

class KeywordDecorator:
    """ decorator for setting function attributes. """
    def __init__(self, keywords, lastname=None):
        self._keywords = keywords
        self._lastname = lastname

    def __call__(self, func=None, **kwargs):
        if func is None:
            kw = self._keywords.copy()
            kw.update(kwargs)
            return KeywordDecorator(kw)
        elif not hasattr(func, 'func_dict'):
            kw = self._keywords.copy()
            name = self._lastname
            if name is None:
                name = "mark"
            kw[name] = func
            return KeywordDecorator(kw)
        func.func_dict.update(self._keywords)
        return func 

    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name)
        kw = self._keywords.copy()
        kw[name] = True
        return self.__class__(kw, lastname=name)

def test_pytest_mark_getattr():
    mark = KeywordDecorator({})
    def f(): pass

    mark.hello(f)
    assert f.hello == True

    mark.hello("test")(f)
    assert f.hello == "test"

    py.test.raises(AttributeError, "mark._hello")
    py.test.raises(AttributeError, "mark.__str__")

def test_pytest_mark_call():
    mark = KeywordDecorator({})
    def f(): pass
    mark(x=3)(f)
    assert f.x == 3
    def g(): pass
    mark(g)
    assert not g.func_dict

    mark.hello(f)
    assert f.hello == True

    mark.hello("test")(f)
    assert f.hello == "test"

    mark("x1")(f)
    assert f.mark == "x1"

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
