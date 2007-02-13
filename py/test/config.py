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
    """ central hub for dealing with configuration/initialization data. """ 
    Option = optparse.Option

    def __init__(self): 
        self.option = CmdOptions()
        self._parser = optparse.OptionParser(
            usage="usage: %prog [options] [query] [filenames of tests]")
        self._conftest = Conftest()
        self._initialized = False

    def parse(self, args): 
        """ parse cmdline arguments into this config object. 
            Note that this can only be called once per testing process. 
        """ 
        assert not self._initialized, (
                "can only parse cmdline args once per Config object")
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

    def _initdirect(self, topdir, repr, coltrails=None):
        assert not self._initialized
        self._initialized = True
        self.topdir = py.path.local(topdir)
        self._mergerepr(repr)
        self._coltrails = coltrails 

    def getcolitems(self):
        """ return initial collectors. """
        trails = getattr(self, '_coltrails', None)
        return [self._getcollector(path) for path in (trails or self.args)]

    def _getcollector(self, path):
        if isinstance(path, tuple):
            relpath, names = path
            fspath = self.topdir.join(relpath)
            col = self._getcollector(fspath)
        else:
            path = py.path.local(path)
            assert path.check(), "%s: path does not exist" %(path,)
            col = self._getrootcollector(path)
            names = path.relto(col.fspath).split(path.sep)
        return col._getitembynames(names)

    def _getrootcollector(self, path):
        pkgpath = path.pypkgpath()
        if pkgpath is None:
            pkgpath = path.check(file=1) and path.dirpath() or path
        col = self._conftest.rget("Directory", pkgpath)(pkgpath)
        col._config = self
        return col 

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

    def initsession(self):
        """ return an initialized session object. """
        cls = self._getsessionclass()
        session = cls(self)
        session.fixoptions()
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
        name = 'TerminalSession'
        if self.option.dist:
            name = 'RSession'
        else:
            optnames = 'startserver runbrowser apigen restreport boxed'.split()
            for opt in optnames:
                if getattr(self.option, opt, False):
                    name = 'LSession'
                    break
            else:
                if self.getvalue('dist_boxed'):
                    name = 'LSession'
                if self.option.looponfailing:
                    name = 'RemoteTerminalSession'
                elif self.option.executable:
                    name = 'RemoteTerminalSession'
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

    def _makerepr(self, conftestnames, optnames=None): 
        """ return a marshallable representation 
            of conftest and cmdline options. 
            if optnames is None, all options
            on self.option will be transferred. 
        """ 
        conftestdict = {}
        for name in conftestnames: 
            value = self.getvalue(name)
            checkmarshal(name, value)
            conftestdict[name] = value 
        cmdlineopts = {}
        if optnames is None:
            optnames = dir(self.option)
        for name in optnames: 
            if not name.startswith("_"):
                value = getattr(self.option, name)
                checkmarshal(name, value)
                cmdlineopts[name] = value
        l = []
        for path in self.args:
            path = py.path.local(path)
            l.append(path.relto(self.topdir)) 
        return l, conftestdict, cmdlineopts

    def _mergerepr(self, repr): 
        """ merge in the conftest and cmdline option values
            found in the given representation (produced
            by _makerepr above).  

            The repr-contained conftest values are
            stored on the default conftest module (last
            priority) and the cmdline options on self.option. 
        """
        class override:
            def __init__(self, d):
                self.__dict__.update(d)
                self.__file__ = "<options from remote>"
        args, conftestdict, cmdlineopts = repr
        self.args = [self.topdir.join(x) for x in args]
        self._conftest.setinitial(self.args)
        self._conftest._path2confmods[None].append(override(conftestdict))
        for name, val in cmdlineopts.items(): 
            setattr(self.option, name, val) 

    def get_collector_trail(self, collector):
        """ provide a trail relative to the topdir, 
            which can be used to reconstruct the
            collector (possibly on a different host
            starting from a different topdir). 
        """ 
        chain = collector.listchain()
        relpath = chain[0].fspath.relto(self.topdir)
        if not relpath:
            if chain[0].fspath == self.topdir:
                relpath = "."
            else:
                raise ValueError("%r not relative to %s" 
                         %(chain[0], self.topdir))
        return relpath, tuple([x.name for x in chain[1:]])

    def _startcapture(self, colitem, path=None):
        if not self.option.nocapture:
            assert not hasattr(colitem, '_capture')
            iocapture = self.getvalue("conf_iocapture", path=path)
            if iocapture == "fd": 
                capture = py.io.StdCaptureFD()
            elif iocapture == "sys":
                capture = py.io.StdCapture()
            else:
                raise ValueError("unknown io capturing: " + iocapture)
            colitem._capture = capture

    def _finishcapture(self, colitem):
        if hasattr(colitem, '_capture'):
            capture = colitem._capture 
            del colitem._capture 
            colitem._captured_out, colitem._captured_err = capture.reset()

# this is the one per-process instance of py.test configuration 
config_per_process = Config()

# default import paths for sessions 

TerminalSession = 'py.__.test.terminal.terminal'
RemoteTerminalSession = 'py.__.test.terminal.remote'
RSession = 'py.__.test.rsession.rsession'
LSession = 'py.__.test.rsession.rsession'

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
        return p
    else:
        return pkgdir.dirpath()
