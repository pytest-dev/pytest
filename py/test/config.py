import py, os
from conftesthandle import Conftest

from py.__.test import parseopt
from py.__.misc.warn import APIWARN
from py.__.test.runner import SetupState

def ensuretemp(string, dir=1): 
    """ return temporary directory path with
        the given string as the trailing part. 
    """ 
    return py.test.config.ensuretemp(string, dir=dir)
  
class CmdOptions(object):
    """ pure container instance for holding cmdline options 
        as attributes. 
    """
    def __repr__(self):
        return "<CmdOptions %r>" %(self.__dict__,)

class Error(Exception):
    """ Test Configuration Error. """

class Config(object): 
    """ central bus for dealing with configuration/initialization data. """ 
    Option = py.compat.optparse.Option # deprecated
    Error = Error
    basetemp = None
    _sessionclass = None

    def __init__(self, pytestplugins=None, topdir=None): 
        self.option = CmdOptions()
        self.topdir = topdir
        self._parser = parseopt.Parser(
            usage="usage: %prog [options] [file_or_dir] [file_or_dir] [...]",
            processopt=self._processopt,
        )
        if pytestplugins is None:
            pytestplugins = py.test._PytestPlugins()
        assert isinstance(pytestplugins, py.test._PytestPlugins)
        self.bus = pytestplugins.pyplugins
        self.pytestplugins = pytestplugins
        self._conftest = Conftest(onimport=self._onimportconftest)
        self._setupstate = SetupState() 
        self.api = pytestplugins._getapi()

    def _onimportconftest(self, conftestmodule):
        self.trace("loaded conftestmodule %r" %(conftestmodule,))
        self.pytestplugins.consider_conftest(conftestmodule)

    def trace(self, msg):
        if getattr(self.option, 'traceconfig', None):
            self.bus.notify("trace", "config", msg) 

    def _processopt(self, opt):
        if hasattr(opt, 'default') and opt.dest:
            val = os.environ.get("PYTEST_OPTION_" + opt.dest.upper(), None)
            if val is not None:
                if opt.type == "int":
                    val = int(val)
                elif opt.type == "long":
                    val = long(val)
                elif opt.type == "float":
                    val = float(val)
                elif not opt.type and opt.action in ("store_true", "store_false"):
                    val = eval(val)
                opt.default = val 
            else:
                name = "pytest_option_" + opt.dest
                try:
                    opt.default = self._conftest.rget(name)
                except (ValueError, KeyError):
                    pass
            if not hasattr(self.option, opt.dest):
                setattr(self.option, opt.dest, opt.default)

    def _preparse(self, args):
        self._conftest.setinitial(args) 
        self.pytestplugins.consider_env()
        self.pytestplugins.do_addoption(self._parser)

    def parse(self, args): 
        """ parse cmdline arguments into this config object. 
            Note that this can only be called once per testing process. 
        """ 
        assert not hasattr(self, 'args'), (
                "can only parse cmdline args at most once per Config object")
        self._preparse(args)
        args = self._parser.parse_setoption(args, self.option)
        if not args:
            args.append(py.std.os.getcwd())
        self.topdir = gettopdir(args)
        self.args = [py.path.local(x) for x in args]

    # config objects are usually pickled across system
    # barriers but they contain filesystem paths. 
    # upon getstate/setstate we take care to do everything
    # relative to "topdir". 
    def __getstate__(self):
        l = []
        for path in self.args:
            path = py.path.local(path)
            l.append(path.relto(self.topdir)) 
        return l, self.option

    def __setstate__(self, repr):
        # warning global side effects:
        # * registering to py lib plugins 
        # * setting py.test.config 
        self.__init__(
            pytestplugins=py.test._PytestPlugins(py._com.pyplugins),
            topdir=py.path.local(),
        )
        # we have to set py.test.config because preparse()
        # might load conftest files which have
        # py.test.config.addoptions() lines in them 
        py.test.config = self 
        args, cmdlineopts = repr 
        args = [self.topdir.join(x) for x in args]
        self.option = cmdlineopts
        self._preparse(args)
        self.args = args 

    def ensuretemp(self, string, dir=True):
        return self.getbasetemp().ensure(string, dir=dir) 

    def getbasetemp(self):
        if self.basetemp is None:
            basetemp = self.option.basetemp 
            if basetemp:
                basetemp = py.path.local(basetemp)
                if not basetemp.check(dir=1):
                    basetemp.mkdir()
            else:
                basetemp = py.path.local.make_numbered_dir(prefix='pytest-')
            self.basetemp = basetemp
        return self.basetemp 

    def mktemp(self, basename, numbered=False):
        basetemp = self.getbasetemp()
        if not numbered:
            return basetemp.mkdir(basename)
        else:
            return py.path.local.make_numbered_dir(prefix=basename + "-", 
                keep=0, rootdir=basetemp, lock_timeout=None)

    def getcolitems(self):
        return [self.getfsnode(arg) for arg in self.args]

    def getfsnode(self, path):
        path = py.path.local(path)
        if not path.check():
            raise self.Error("file not found: %s" %(path,))
        # we want our possibly custom collection tree to start at pkgroot 
        pkgpath = path.pypkgpath()
        if pkgpath is None:
            pkgpath = path.check(file=1) and path.dirpath() or path
        Dir = self._conftest.rget("Directory", pkgpath)
        col = Dir(pkgpath, config=self)
        return col._getfsnode(path)

    def getconftest_pathlist(self, name, path=None):
        """ return a matching value, which needs to be sequence
            of filenames that will be returned as a list of Path
            objects (they can be relative to the location 
            where they were found).
        """
        try:
            mod, relroots = self._conftest.rget_with_confmod(name, path)
        except KeyError:
            return None
        modpath = py.path.local(mod.__file__).dirpath()
        l = []
        for relroot in relroots:
            relroot = relroot.replace("/", py.path.local.sep)
            l.append(modpath.join(relroot, abs=True))
        return l 
             
    def addoptions(self, groupname, *specs): 
        """ add a named group of options to the current testing session. 
            This function gets invoked during testing session initialization. 
        """ 
        APIWARN("1.0", "define plugins to add options", stacklevel=2)
        group = self._parser.addgroup(groupname)
        for opt in specs:
            group._addoption_instance(opt)
        return self.option 

    def addoption(self, *optnames, **attrs):
        return self._parser.addoption(*optnames, **attrs)

    def getvalueorskip(self, name, path=None): 
        """ return getvalue() or call py.test.skip if no value exists. """
        try:
            val = self.getvalue(name, path)
            if val is None:
                raise KeyError(name)
            return val
        except KeyError:
            py.test.skip("no %r value found" %(name,))

    def getvalue(self, name, path=None): 
        """ return 'name' value looked up from the 'options'
            and then from the first conftest file found up 
            the path (including the path itself). 
            if path is None, lookup the value in the initial
            conftest modules found during command line parsing. 
        """
        try:
            return getattr(self.option, name)
        except AttributeError:
            return self._conftest.rget(name, path)

    def setsessionclass(self, cls):
        if self._sessionclass is not None:
            raise ValueError("sessionclass already set to: %r" %(
                self._sessionclass))
        self._sessionclass = cls

    def initsession(self):
        """ return an initialized session object. """
        cls = self._sessionclass 
        if cls is None:
            from py.__.test.session import Session
            cls = Session
        session = cls(self)
        self.trace("instantiated session %r" % session)
        return session

    def _reparse(self, args):
        """ this is used from tests that want to re-invoke parse(). """
        #assert args # XXX should not be empty
        global config_per_process
        oldconfig = py.test.config
        try:
            config_per_process = py.test.config = Config()
            config_per_process.basetemp = self.mktemp("reparse", numbered=True)
            config_per_process.parse(args) 
            return config_per_process
        finally: 
            config_per_process = py.test.config = oldconfig 

    def _getcapture(self, path=None):
        if self.option.nocapture:
            iocapture = "no" 
        else:
            iocapture = self.getvalue("iocapture", path=path)
        if iocapture == "fd": 
            return py.io.StdCaptureFD()
        elif iocapture == "sys":
            return py.io.StdCapture()
        elif iocapture == "no": 
            return py.io.StdCapture(out=False, err=False, in_=False)
        else:
            raise self.Error("unknown io capturing: " + iocapture)

    def getxspecs(self):
        xspeclist = []
        for xspec in self.getvalue("tx"):
            i = xspec.find("*")
            try:
                num = int(xspec[:i])
            except ValueError:
                xspeclist.append(xspec)
            else:
                xspeclist.extend([xspec[i+1:]] * num)
        if not xspeclist:
            raise self.Error("MISSING test execution (tx) nodes: please specify --tx")
        return [py.execnet.XSpec(x) for x in xspeclist]

    def getrsyncdirs(self):
        config = self 
        roots = config.option.rsyncdir
        conftestroots = config.getconftest_pathlist("rsyncdirs")
        if conftestroots:
            roots.extend(conftestroots)
        pydir = py.path.local(py.__file__).dirpath()
        roots = [py.path.local(root) for root in roots]
        for root in roots:
            if not root.check():
                raise config.Error("rsyncdir doesn't exist: %r" %(root,))
            if pydir is not None and root.basename == "py":
                if root != pydir:
                    raise config.Error("root %r conflicts with imported %r" %(root, pydir))
                pydir = None
        if pydir is not None:
            roots.append(pydir)
        return roots 

    def guardedcall(self, func):
        excinfo = result = None
        capture = self._getcapture()
        try:
            try:
                result = func()
            except KeyboardInterrupt:
                raise
            except:
                excinfo = py.code.ExceptionInfo()
        finally:
            stdout, stderr = capture.reset()
        return CallResult(result, excinfo, stdout, stderr)

class CallResult:
    def __init__(self, result, excinfo, stdout, stderr):
        self.stdout = stdout 
        self.stderr = stderr
        self.outerr = (self.stdout, self.stderr)
        self.excinfo = excinfo
        if excinfo is None:
            self.result = result 
    
#
# helpers
#

def checkmarshal(name, value):
    try:
        py.std.marshal.dumps(value)
    except ValueError:
        raise ValueError("%s=%r is not marshallable" %(name, value))

def gettopdir(args): 
    """ return the top directory for the given paths.
        if the common base dir resides in a python package 
        parent directory of the root package is returned. 
    """
    args = [py.path.local(arg) for arg in args]
    p = reduce(py.path.local.common, args)
    assert p, "cannot determine common basedir of %s" %(args,)
    pkgdir = p.pypkgpath()
    if pkgdir is None:
        if p.check(file=1):
            p = p.dirpath()
        return p
    else:
        return pkgdir.dirpath()


# this is the one per-process instance of py.test configuration 
config_per_process = Config(
    pytestplugins=py.test._PytestPlugins(py._com.pyplugins)
)

