import py, os
from pytest.pluginmanager import PluginManager
import optparse

class Parser:
    """ Parser for command line arguments. """

    def __init__(self, usage=None, processopt=None):
        self._anonymous = OptionGroup("custom options", parser=self)
        self._groups = []
        self._processopt = processopt
        self._usage = usage
        self.hints = []

    def processoption(self, option):
        if self._processopt:
            if option.dest:
                self._processopt(option)

    def addnote(self, note):
        self._notes.append(note)

    def getgroup(self, name, description="", after=None):
        for group in self._groups:
            if group.name == name:
                return group
        group = OptionGroup(name, description, parser=self)
        i = 0
        for i, grp in enumerate(self._groups):
            if grp.name == after:
                break
        self._groups.insert(i+1, group)
        return group

    addgroup = getgroup
    def addgroup(self, name, description=""):
        py.log._apiwarn("1.1", "use getgroup() which gets-or-creates")
        return self.getgroup(name, description)

    def addoption(self, *opts, **attrs):
        """ add an optparse-style option. """
        self._anonymous.addoption(*opts, **attrs)

    def parse(self, args):
        optparser = MyOptionParser(self)
        groups = self._groups + [self._anonymous]
        for group in groups:
            if group.options:
                desc = group.description or group.name
                optgroup = optparse.OptionGroup(optparser, desc)
                optgroup.add_options(group.options)
                optparser.add_option_group(optgroup)
        return optparser.parse_args([str(x) for x in args])

    def parse_setoption(self, args, option):
        parsedoption, args = self.parse(args)
        for name, value in parsedoption.__dict__.items():
            setattr(option, name, value)
        return args


class OptionGroup:
    def __init__(self, name, description="", parser=None):
        self.name = name
        self.description = description
        self.options = []
        self.parser = parser

    def addoption(self, *optnames, **attrs):
        """ add an option to this group. """
        option = optparse.Option(*optnames, **attrs)
        self._addoption_instance(option, shortupper=False)

    def _addoption(self, *optnames, **attrs):
        option = optparse.Option(*optnames, **attrs)
        self._addoption_instance(option, shortupper=True)

    def _addoption_instance(self, option, shortupper=False):
        if not shortupper:
            for opt in option._short_opts:
                if opt[0] == '-' and opt[1].islower():
                    raise ValueError("lowercase shortoptions reserved")
        if self.parser:
            self.parser.processoption(option)
        self.options.append(option)


class MyOptionParser(optparse.OptionParser):
    def __init__(self, parser):
        self._parser = parser
        optparse.OptionParser.__init__(self, usage=parser._usage)
    def format_epilog(self, formatter):
        hints = self._parser.hints
        if hints:
            s = "\n".join(["hint: " + x for x in hints]) + "\n"
            s = "\n" + s + "\n"
            return s
        return ""
class Conftest(object):
    """ the single place for accessing values and interacting
        towards conftest modules from py.test objects.
    """
    def __init__(self, onimport=None, confcutdir=None):
        self._path2confmods = {}
        self._onimport = onimport
        self._conftestpath2mod = {}
        self._confcutdir = confcutdir
        self._md5cache = {}

    def setinitial(self, args):
        """ try to find a first anchor path for looking up global values
            from conftests. This function is usually called _before_
            argument parsing.  conftest files may add command line options
            and we thus have no completely safe way of determining
            which parts of the arguments are actually related to options
            and which are file system paths.  We just try here to get
            bootstrapped ...
        """
        current = py.path.local()
        opt = '--confcutdir'
        for i in range(len(args)):
            opt1 = str(args[i])
            if opt1.startswith(opt):
                if opt1 == opt:
                    if len(args) > i:
                        p = current.join(args[i+1], abs=True)
                elif opt1.startswith(opt + "="):
                    p = current.join(opt1[len(opt)+1:], abs=1)
                self._confcutdir = p
                break
        for arg in args + [current]:
            if hasattr(arg, 'startswith') and arg.startswith("--"):
                continue
            anchor = current.join(arg, abs=1)
            if anchor.check(): # we found some file object
                self._path2confmods[None] = self.getconftestmodules(anchor)
                # let's also consider test* dirs
                if anchor.check(dir=1):
                    for x in anchor.listdir("test*"):
                        if x.check(dir=1):
                            self.getconftestmodules(x)
                break
        else:
            assert 0, "no root of filesystem?"

    def getconftestmodules(self, path):
        """ return a list of imported conftest modules for the given path.  """
        try:
            clist = self._path2confmods[path]
        except KeyError:
            if path is None:
                raise ValueError("missing default confest.")
            dp = path.dirpath()
            clist = []
            if dp != path:
                cutdir = self._confcutdir
                if cutdir and path != cutdir and not path.relto(cutdir):
                    pass
                else:
                    conftestpath = path.join("conftest.py")
                    if conftestpath.check(file=1):
                        key = conftestpath.computehash()
                        # XXX logging about conftest loading
                        if key not in self._md5cache:
                            clist.append(self.importconftest(conftestpath))
                            self._md5cache[key] = conftestpath
                        else:
                            # use some kind of logging
                            print ("WARN: not loading %s" % conftestpath)
                clist[:0] = self.getconftestmodules(dp)
            self._path2confmods[path] = clist
        # be defensive: avoid changes from caller side to
        # affect us by always returning a copy of the actual list
        return clist[:]

    def rget(self, name, path=None):
        mod, value = self.rget_with_confmod(name, path)
        return value

    def rget_with_confmod(self, name, path=None):
        modules = self.getconftestmodules(path)
        modules.reverse()
        for mod in modules:
            try:
                return mod, getattr(mod, name)
            except AttributeError:
                continue
        raise KeyError(name)

    def importconftest(self, conftestpath):
        assert conftestpath.check(), conftestpath
        try:
            return self._conftestpath2mod[conftestpath]
        except KeyError:
            if not conftestpath.dirpath('__init__.py').check(file=1):
                # HACK: we don't want any "globally" imported conftest.py,
                #       prone to conflicts and subtle problems
                modname = str(conftestpath).replace('.', conftestpath.sep)
                mod = conftestpath.pyimport(modname=modname)
            else:
                mod = conftestpath.pyimport()
            self._conftestpath2mod[conftestpath] = mod
            dirpath = conftestpath.dirpath()
            if dirpath in self._path2confmods:
                for path, mods in self._path2confmods.items():
                    if path and path.relto(dirpath) or path == dirpath:
                        assert mod not in mods
                        mods.append(mod)
            self._postimport(mod)
            return mod

    def _postimport(self, mod):
        if self._onimport:
            self._onimport(mod)
        return mod


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
        self._parser = Parser(
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


