import py

# test support code
def params(funcarglist):
    def wrapper(function):
        function.funcarglist = funcarglist
        return function
    return wrapper

def pytest_generate_tests(metafunc):
    for funcargs in getattr(metafunc.function, 'funcarglist', ()):
        metafunc.addcall(funcargs=funcargs)


# actual test code
 
class TestClass:
    @params([dict(a=1, b=2), dict(a=3, b=3), dict(a=5, b=4)], )
    def test_equals(self, a, b):
        assert a == b

    @params([dict(a=1, b=0), dict(a=3, b=2)])
    def test_zerodivision(self, a, b):
        py.test.raises(ZeroDivisionError, "a/b")

