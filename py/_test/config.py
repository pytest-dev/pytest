import py, os
from py._test.conftesthandle import Conftest
from py._test.pluginmanager import PluginManager
from py._test import parseopt

def ensuretemp(string, dir=1):
    """ (deprecated) return temporary directory path with
        the given string as the trailing part.  It is usually
        better to use the 'tmpdir' function argument which will
        take care to provide empty unique directories for each
        test call even if the test is called multiple times.
    """
    #py.log._apiwarn(">1.1", "use tmpdir function argument")
    return py.test.config.ensuretemp(string, dir=dir)

class CmdOptions(object):
    """ holds cmdline options as attributes."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        return "<CmdOptions %r>" %(self.__dict__,)

class Error(Exception):
    """ Test Configuration Error. """

class Config(object):
    """ access to config values, pluginmanager and plugin hooks.  """
    Option = py.std.optparse.Option
    Error = Error
    basetemp = None
    _sessionclass = None

    def __init__(self):
        self.option = CmdOptions()
        self._parser = parseopt.Parser(
            usage="usage: %prog [options] [file_or_dir] [file_or_dir] [...]",
            processopt=self._processopt,
        )
        self.pluginmanager = PluginManager()
        self._conftest = Conftest(onimport=self._onimportconftest)
        self.hook = self.pluginmanager.hook

    def _onimportconftest(self, conftestmodule):
        self.trace("loaded conftestmodule %r" %(conftestmodule,))
        self.pluginmanager.consider_conftest(conftestmodule)

    def _getmatchingplugins(self, fspath):
        allconftests = self._conftest._conftestpath2mod.values()
        plugins = [x for x in self.pluginmanager.getplugins()
                        if x not in allconftests]
        plugins += self._conftest.getconftestmodules(fspath)
        return plugins

    def trace(self, msg):
        if getattr(self.option, 'traceconfig', None):
            self.hook.pytest_trace(category="config", msg=msg)

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
                name = "option_" + opt.dest
                try:
                    opt.default = self._conftest.rget(name)
                except (ValueError, KeyError):
                    pass
            if not hasattr(self.option, opt.dest):
                setattr(self.option, opt.dest, opt.default)

    def _preparse(self, args):
        self.pluginmanager.consider_setuptools_entrypoints()
        self.pluginmanager.consider_env()
        self.pluginmanager.consider_preparse(args)
        self._conftest.setinitial(args)
        self.pluginmanager.do_addoption(self._parser)

    def parse(self, args):
        """ parse cmdline arguments into this config object.
            Note that this can only be called once per testing process.
        """
        assert not hasattr(self, 'args'), (
                "can only parse cmdline args at most once per Config object")
        self._preparse(args)
        self._parser.hints.extend(self.pluginmanager._hints)
        args = self._parser.parse_setoption(args, self.option)
        if not args:
            args.append(py.std.os.getcwd())
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
            return py.path.local.make_numbered_dir(prefix=basename,
                keep=0, rootdir=basetemp, lock_timeout=None)

    def _getcollectclass(self, name, path):
        try:
            cls = self._conftest.rget(name, path)
        except KeyError:
            return getattr(py.test.collect, name)
        else:
            py.log._apiwarn(">1.1", "%r was found in a conftest.py file, "
                "use pytest_collect hooks instead." % (cls,))
            return cls

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
            if not isinstance(relroot, py.path.local):
                relroot = relroot.replace("/", py.path.local.sep)
                relroot = modpath.join(relroot, abs=True)
            l.append(relroot)
        return l

    def addoptions(self, groupname, *specs):
        """ add a named group of options to the current testing session.
            This function gets invoked during testing session initialization.
        """
        py.log._apiwarn("1.0", "define pytest_addoptions(parser) to add options", stacklevel=2)
        group = self._parser.getgroup(groupname)
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

#
# helpers
#

def onpytestaccess():
    # it's enough to have our containing module loaded as
    # it initializes a per-process config instance
    # which loads default plugins which add to py.test.*
    pass

# a default per-process instance of py.test configuration
config_per_process = Config()
