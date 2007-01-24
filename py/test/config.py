from __future__ import generators

import py
from conftesthandle import Conftest

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
    conftest = Conftest()

    def __init__(self): 
        self.option = CmdOptions()
        self._parser = optparse.OptionParser(
            usage="usage: %prog [options] [query] [filenames of tests]")
        self._parsed = False

    def parse(self, args): 
        """ parse cmdline arguments into this config object. 
            Note that this can only be called once per testing process. 
        """ 
        assert not self._parsed, (
                "can only parse cmdline args once per Config object")
        self._parsed = True
        self.conftest.setinitial(args) 
        self.conftest.lget('adddefaultoptions')()
        args = [str(x) for x in args]
        self._origargs = args
        cmdlineoption, remaining = self._parser.parse_args(args) 
        self.option.__dict__.update(vars(cmdlineoption))
        fixoptions(self.option)  # XXX fixing should be moved to sessions
        if not remaining: 
            remaining.append(py.std.os.getcwd()) 
        self.remaining = remaining 

    def addoptions(self, groupname, *specs): 
        """ add a named group of options to the current testing session. 
            This function gets invoked during testing session initialization. 
        """ 
        optgroup = optparse.OptionGroup(self._parser, groupname) 
        optgroup.add_options(specs) 
        self._parser.add_option_group(optgroup)
        for opt in specs: 
            if hasattr(opt, 'default') and opt.dest:
                setattr(self.option, opt.dest, opt.default) 
        return self.option

    def getvalue(self, name, path=None): 
        """ return 'name' value looked up from the first conftest file 
            found up the path (including the path itself). 
            if path is None, lookup the value in the initial
            conftest modules found during command line parsing. 
        """
        return self.conftest.rget(name, path) 

    def getsessionclass(self): 
        """ return Session class determined from cmdline options
            and looked up in initial config modules. 
        """
        sessionname = self.option.session + 'Session'
        try:
            return self.conftest.rget(sessionname) 
        except KeyError: 
            pass
        sessionimportpaths = self.conftest.lget('sessionimportpaths')
        importpath = sessionimportpaths[sessionname]
        mod = __import__(importpath, None, None, ['__doc__'])
        return getattr(mod, sessionname) 

    def _reparse(self, args):
        """ this is used from tests that want to re-invoke parse(). """
        global config 
        oldconfig = py.test.config 
        try:
            config = py.test.config = Config()
            config.parse(args) 
            return config
        finally: 
            config = py.test.config = oldconfig 

# this is the one per-process instance of py.test configuration 
config = Config()

#
# helpers
#

def fixoptions(option):
    """ sanity checks and making option values canonical. """
    if option.looponfailing and option.usepdb:
        raise ValueError, "--looponfailing together with --pdb not supported yet."
    if option.executable and option.usepdb:
        raise ValueError, "--exec together with --pdb not supported yet."

    # setting a correct executable
    remote = False
    if option.executable is not None:
        remote = True 
        exe = py.path.local(py.std.os.path.expanduser(option.executable))
        if not exe.check():
            exe = py.path.local.sysfind(option.executable)
        assert exe.check()
        option.executable = exe
    else: 
        option.executable = py.std.sys.executable 

    if option.usepdb:
        if not option.nocapture:
            print "--usepdb currently implies --nocapture"
            option.nocapture = True

    # make information available about wether we should/will be remote 
    option._remote = remote or option.looponfailing
    option._fromremote = False 

    # setting a correct frontend session 
    if option.session:
        name = option.session
    elif option.tkinter:
        name = 'tkinter'
    else:
        name = 'terminal'
    name = name.capitalize() 
    option.session = name 

    if option.runbrowser and not option.startserver:
        print "Cannot point browser when not starting server"
        option.startserver = True
    
