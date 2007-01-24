from py import test

def somefunc(x, y):
    assert x == y

class TestClass:
    def test_raises(self):
        test.raises(ValueError, "int('qwe')")

    def test_raises_exec(self):
        test.raises(ValueError, "a,x = []") 

    def test_raises_syntax_error(self):
        test.raises(SyntaxError, "qwe qwe qwe")

    def test_raises_function(self):
        test.raises(ValueError, int, 'hello')

