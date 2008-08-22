from __future__ import generators

import py
from conftesthandle import Conftest
from py.__.test.defaultconftest import adddefaultoptions

optparse = py.compat.optparse

# XXX move to Config class
basetemp = None
def ensuretemp(string, dir=1): 
    """ return temporary directory path with
        the given string as the trailing part. 
    """ 
    global basetemp
    if basetemp is None: 
        basetemp = py.path.local.make_numbered_dir(prefix='pytest-')
    return basetemp.ensure(string, dir=dir) 
  
class CmdOptions(object):
    """ pure container instance for holding cmdline options 
        as attributes. 
    """
    def __repr__(self):
        return "<CmdOptions %r>" %(self.__dict__,)

class Config(object): 
    """ central bus for dealing with configuration/initialization data. """ 
    Option = optparse.Option
    _initialized = False

    def __init__(self): 
        self.option = CmdOptions()
        self._parser = optparse.OptionParser(
            usage="usage: %prog [options] [query] [filenames of tests]")
        self._conftest = Conftest()

    def parse(self, args): 
        """ parse cmdline arguments into this config object. 
            Note that this can only be called once per testing process. 
        """ 
        assert not self._initialized, (
                "can only parse cmdline args at most once per Config object")
        self._initialized = True
        adddefaultoptions(self)
        self._conftest.setinitial(args) 
        args = [str(x) for x in args]
        cmdlineoption, args = self._parser.parse_args(args) 
        self.option.__dict__.update(vars(cmdlineoption))
        if not args:
            args.append(py.std.os.getcwd())
        self.topdir = gettopdir(args)
        self.args = args 

    # config objects are usually pickled across system
    # barriers but they contain filesystem paths. 
    # upon getstate/setstate we take care to do everything
    # relative to our "topdir". 
    def __getstate__(self):
        return self._makerepr()
    def __setstate__(self, repr):
        self._repr = repr

    def _initafterpickle(self, topdir):
        self.__init__()
        self._initialized = True
        self.topdir = py.path.local(topdir)
        self._mergerepr(self._repr)
        del self._repr 

    def _makerepr(self):
        l = []
        for path in self.args:
            path = py.path.local(path)
            l.append(path.relto(self.topdir)) 
        return l, self.option

    def _mergerepr(self, repr): 
        # before any conftests are loaded we 
        # need to set the per-process singleton 
        # (also seens py.test.config) to have consistent
        # option handling 
        global config_per_process
        config_per_process = self  
        args, cmdlineopts = repr 
        self.args = [self.topdir.join(x) for x in args]
        self.option = cmdlineopts
        self._conftest.setinitial(self.args)

    def getfsnode(self, path):
        path = py.path.local(path)
        assert path.check(), "%s: path does not exist" %(path,)
        # we want our possibly custom collection tree to start at pkgroot 
        pkgpath = path.pypkgpath()
        if pkgpath is None:
            pkgpath = path.check(file=1) and path.dirpath() or path
        Dir = self._conftest.rget("Directory", pkgpath)
        col = Dir(pkgpath, config=self)
        names = path.relto(col.fspath).split(path.sep)
        return col._getitembynames(names)

    def getvalue_pathlist(self, name, path=None):
        """ return a matching value, which needs to be sequence
            of filenames that will be returned as a list of Path
            objects (they can be relative to the location 
            where they were found).
        """
        try:
            return getattr(self.option, name)
        except AttributeError:
            try:
                mod, relroots = self._conftest.rget_with_confmod(name, path)
            except KeyError:
                return None
            modpath = py.path.local(mod.__file__).dirpath()
            return [modpath.join(x, abs=True) for x in relroots]
             
    def addoptions(self, groupname, *specs): 
        """ add a named group of options to the current testing session. 
            This function gets invoked during testing session initialization. 
        """ 
        for spec in specs:
            for shortopt in spec._short_opts:
                if not shortopt.isupper(): 
                    raise ValueError(
                        "custom options must be capital letter "
                        "got %r" %(spec,)
                    )
        return self._addoptions(groupname, *specs)

    def _addoptions(self, groupname, *specs):
        optgroup = optparse.OptionGroup(self._parser, groupname) 
        optgroup.add_options(specs) 
        self._parser.add_option_group(optgroup)
        for opt in specs: 
            if hasattr(opt, 'default') and opt.dest:
                if not hasattr(self.option, opt.dest):
                    setattr(self.option, opt.dest, opt.default) 
        return self.option

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

    def initreporter(self, bus):
        if self.option.collectonly:
            from py.__.test.report.collectonly import Reporter
        else:
            from py.__.test.report.terminal import Reporter 
        rep = Reporter(self, bus=bus)
        return rep

    def initsession(self):
        """ return an initialized session object. """
        cls = self._getsessionclass()
        session = cls(self)
        session.fixoptions()
        session.reporter = self.initreporter(session.bus)
        return session

    def _getsessionclass(self): 
        """ return Session class determined from cmdline options
            and looked up in initial config modules. 
        """
        if self.option.session is not None:
            return self._conftest.rget(self.option.session)
        else:
            name = self._getsessionname()
            try:
                return self._conftest.rget(name)
            except KeyError:
                pass
            importpath = globals()[name]
            mod = __import__(importpath, None, None, '__doc__')
            return getattr(mod, name)

    def _getsessionname(self):
        """ return default session name as determined from options. """
        if self.option.collectonly:
            name = 'Session'
        elif self.option.looponfailing:
            name = 'LooponfailingSession'
        elif self.option.numprocesses or self.option.dist or self.option.executable: 
            name = 'DSession'
        else:
            name = 'Session'
        return name

    def _reparse(self, args):
        """ this is used from tests that want to re-invoke parse(). """
        #assert args # XXX should not be empty
        global config_per_process
        oldconfig = py.test.config
        try:
            config_per_process = py.test.config = Config()
            config_per_process.parse(args) 
            return config_per_process
        finally: 
            config_per_process = py.test.config = oldconfig 

    def _getcapture(self, path=None):
        if self.option.nocapture:
            iocapture = "no" 
        else:
            iocapture = self.getvalue("conf_iocapture", path=path)
        if iocapture == "fd": 
            return py.io.StdCaptureFD()
        elif iocapture == "sys":
            return py.io.StdCapture()
        elif iocapture == "no": 
            return py.io.StdCapture(out=False, err=False, in_=False)
        else:
            raise ValueError("unknown io capturing: " + iocapture)

    
    def gettracedir(self):
        """ return a tracedirectory or None, depending on --tracedir. """
        if self.option.tracedir is not None:
            return py.path.local(self.option.tracedir)

    def maketrace(self, name, flush=True):
        """ return a tracedirectory or None, depending on --tracedir. """
        tracedir = self.gettracedir()
        if tracedir is None:
            return NullTracer()
        tracedir.ensure(dir=1)
        return Tracer(tracedir.join(name), flush=flush)

class Tracer(object):
    file = None
    def __init__(self, path, flush=True):
        self.file = path.open(mode='w')
        self.flush = flush
       
    def __call__(self, *args):
        time = round(py.std.time.time(), 3)
        print >>self.file, time, " ".join(map(str, args))
        if self.flush:
            self.file.flush()

    def close(self):
        self.file.close()

class NullTracer:
    def __call__(self, *args):
        pass
    def close(self):
        pass
    
# this is the one per-process instance of py.test configuration 
config_per_process = Config()

# default import paths for sessions 

Session = 'py.__.test.session'
LooponfailingSession = 'py.__.test.looponfail.remote'
DSession = 'py.__.test.dsession.dsession'

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
