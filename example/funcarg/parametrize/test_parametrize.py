import py

def pytest_generate_tests(metafunc):
    for funcargs in metafunc.cls.params[metafunc.function.__name__]:
        metafunc.addcall(funcargs=funcargs)
 
class TestClass:
    params = {
        'test_equals': [dict(a=1, b=2), dict(a=3, b=3), dict(a=5, b=4)],
        'test_zerodivision': [dict(a=1, b=0), dict(a=3, b=2)],
    }
   
    def test_equals(self, a, b):
        assert a == b

    def test_zerodivision(self, a, b):
        py.test.raises(ZeroDivisionError, "a/b")
