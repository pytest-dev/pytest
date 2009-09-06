"""
    provide temporary directories to test functions and methods. 

example:

    pytest_plugins = "pytest_tmpdir" 

    def test_plugin(tmpdir):
        tmpdir.join("hello").write("hello")

"""
import py

def pytest_funcarg__tmpdir(request):
    name = request.function.__name__ 
    return request.config.mktemp(name, numbered=True)
