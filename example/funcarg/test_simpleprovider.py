# ./test_simpleprovider.py
def pytest_funcarg__myfuncarg(request):
    return 42

def test_function(myfuncarg):
    assert myfuncarg == 17

