""" support for providing temporary directories to test functions.  """
import pytest, py
from _pytest.monkeypatch import monkeypatch

class TempdirHandler:
    def __init__(self, config):
        self.config = config
        self.trace = config.trace.get("tmpdir")

    def ensuretemp(self, string, dir=1):
        """ (deprecated) return temporary directory path with
            the given string as the trailing part.  It is usually
            better to use the 'tmpdir' function argument which
            provides an empty unique-per-test-invocation directory
            and is guaranteed to be empty.
        """
        #py.log._apiwarn(">1.1", "use tmpdir function argument")
        return self.getbasetemp().ensure(string, dir=dir)

    def mktemp(self, basename, numbered=True):
        basetemp = self.getbasetemp()
        if not numbered:
            p = basetemp.mkdir(basename)
        else:
            p = py.path.local.make_numbered_dir(prefix=basename,
                keep=0, rootdir=basetemp, lock_timeout=None)
        self.trace("mktemp", p)
        return p

    def getbasetemp(self):
        """ return base temporary directory. """
        try:
            return self._basetemp
        except AttributeError:
            basetemp = self.config.option.basetemp
            if basetemp:
                basetemp = py.path.local(basetemp)
                if basetemp.check():
                    basetemp.remove()
                basetemp.mkdir()
            else:
                basetemp = py.path.local.make_numbered_dir(prefix='pytest-')
            self._basetemp = t = basetemp
            self.trace("new basetemp", t)
            return t

    def finish(self):
        self.trace("finish")
        
def pytest_configure(config):
    mp = monkeypatch()
    t = TempdirHandler(config)
    config._cleanup.extend([mp.undo, t.finish])
    mp.setattr(config, '_tmpdirhandler', t, raising=False)
    mp.setattr(pytest, 'ensuretemp', t.ensuretemp, raising=False)

def pytest_funcarg__tmpdir(request):
    """return a temporary directory path object
    which is unique to each test function invocation,
    created as a sub directory of the base temporary
    directory.  The returned object is a `py.path.local`_
    path object.
    """
    name = request._pyfuncitem.name
    name = py.std.re.sub("[\W]", "_", name)
    x = request.config._tmpdirhandler.mktemp(name, numbered=True)
    return x.realpath()

