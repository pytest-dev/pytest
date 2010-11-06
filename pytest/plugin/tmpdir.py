""" support for providing temporary directories to test functions.  """
import pytest, py

def pytest_configure(config):
    def ensuretemp(string, dir=1):
        """ (deprecated) return temporary directory path with
            the given string as the trailing part.  It is usually
            better to use the 'tmpdir' function argument which will
            take care to provide empty unique directories for each
            test call even if the test is called multiple times.
        """
        #py.log._apiwarn(">1.1", "use tmpdir function argument")
        return config.ensuretemp(string, dir=dir)
    pytest.ensuretemp = ensuretemp

def pytest_funcarg__tmpdir(request):
    """return a temporary directory path object
    unique to each test function invocation,
    created as a sub directory of the base temporary
    directory.  The returned object is a `py.path.local`_
    path object.
    """
    name = request._pyfuncitem.name
    name = py.std.re.sub("[\W]", "_", name)
    x = request.config.mktemp(name, numbered=True)
    return x.realpath()
