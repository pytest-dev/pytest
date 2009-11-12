"""provide temporary directories to test functions. 

usage example::

    def test_plugin(tmpdir):
        tmpdir.join("hello").write("hello")

.. _`py.path.local`: ../../path.html

"""
import py

def pytest_funcarg__tmpdir(request):
    """return a temporary directory path object
    unique to each test function invocation,
    created as a sub directory of the base temporary
    directory.  The returned object is a `py.path.local`_
    path object. 
    """
    name = request.function.__name__ 
    x = request.config.mktemp(name, numbered=True)
    return x.realpath()
