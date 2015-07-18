""" command line options, ini-file and conftest.py processing. """
import argparse
import shlex
import traceback
import types
import warnings

import py
# DON't import pytest here because it causes import cycle troubles
import sys, os
from _pytest import hookspec # the extension point definitions
from _pytest.core import PluginManager

# pytest startup
#
class ConftestImportFailure(Exception):
    def __init__(self, path, excinfo):
        Exception.__init__(self, path, excinfo)
        self.path = path
        self.excinfo = excinfo


def main(args=None, plugins=None):
    """ return exit code, after performing an in-process test run.

    :arg args: list of command line arguments.

    :arg plugins: list of plugin objects to be auto-registered during
                  initialization.
    """
    try:
        config = _prepareconfig(args, plugins)
    except ConftestImportFailure:
        e = sys.exc_info()[1]
        tw = py.io.TerminalWriter(sys.stderr)
        for line in traceback.format_exception(*e.excinfo):
            tw.line(line.rstrip(), red=True)
        tw.line("ERROR: could not load %s\n" % (e.path), red=True)
        return 4
    else:
        return config.hook.pytest_cmdline_main(config=config)

class cmdline:  # compatibility namespace
    main = staticmethod(main)

class UsageError(Exception):
    """ error in pytest usage or invocation"""

_preinit = []

default_plugins = (
     "mark main terminal runner python pdb unittest capture skipping "
     "tmpdir monkeypatch recwarn pastebin helpconfig nose assertion genscript "
     "junitxml resultlog doctest").split()

def _preloadplugins():
    assert not _preinit
    _preinit.append(get_plugin_manager())

def get_plugin_manager():
    if _preinit:
        return _preinit.pop(0)
    # subsequent calls to main will create a fresh instance
    pluginmanager = PytestPluginManager()
    pluginmanager.config = Config(pluginmanager) # XXX attr needed?
    for spec in default_plugins:
        pluginmanager.import_plugin(spec)
    return pluginmanager

def _prepareconfig(args=None, plugins=None):
    if args is None:
        args = sys.argv[1:]
    elif isinstance(args, py.path.local):
        args = [str(args)]
    elif not isinstance(args, (tuple, list)):
        if not isinstance(args, str):
            raise ValueError("not a string or argument list: %r" % (args,))
        args = shlex.split(args)
    pluginmanager = get_plugin_manager()
    try:
        if plugins:
            for plugin in plugins:
                if isinstance(plugin, py.builtin._basestring):
                    pluginmanager.consider_pluginarg(plugin)
                else:
                    pluginmanager.register(plugin)
        return pluginmanager.hook.pytest_cmdline_parse(
                pluginmanager=pluginmanager, args=args)
    except Exception:
        pluginmanager.ensure_shutdown()
        raise

class PytestPluginManager(PluginManager):
    def __init__(self, hookspecs=[hookspec]):
        super(PytestPluginManager, self).__init__(hookspecs=hookspecs)
        self.register(self)
        if os.environ.get('PYTEST_DEBUG'):
            err = sys.stderr
            encoding = getattr(err, 'encoding', 'utf8')
            try:
                err = py.io.dupfile(err, encoding=encoding)
            except Exception:
                pass
            self.set_tracing(err.write)

    def pytest_configure(self, config):
        config.addinivalue_line("markers",
            "tryfirst: mark a hook implementation function such that the "
            "plugin machinery will try to call it first/as early as possible.")
        config.addinivalue_line("markers",
            "trylast: mark a hook implementation function such that the "
            "plugin machinery will try to call it last/as late as possible.")
        for warning in self._warnings:
            config.warn(code="I1", message=warning)


class Parser:
    """ Parser for command line arguments and ini-file values.  """

    def __init__(self, usage=None, processopt=None):
        self._anonymous = OptionGroup("custom options", parser=self)
        self._groups = []
        self._processopt = processopt
        self._usage = usage
        self._inidict = {}
        self._ininames = []

    def processoption(self, option):
        if self._processopt:
            if option.dest:
                self._processopt(option)

    def getgroup(self, name, description="", after=None):
        """ get (or create) a named option Group.

        :name: name of the option group.
        :description: long description for --help output.
        :after: name of other group, used for ordering --help output.

        The returned group object has an ``addoption`` method with the same
        signature as :py:func:`parser.addoption
        <_pytest.config.Parser.addoption>` but will be shown in the
        respective group in the output of ``pytest. --help``.
        """
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

    def addoption(self, *opts, **attrs):
        """ register a command line option.

        :opts: option names, can be short or long options.
        :attrs: same attributes which the ``add_option()`` function of the
           `argparse library
           <http://docs.python.org/2/library/argparse.html>`_
           accepts.

        After command line parsing options are available on the pytest config
        object via ``config.option.NAME`` where ``NAME`` is usually set
        by passing a ``dest`` attribute, for example
        ``addoption("--long", dest="NAME", ...)``.
        """
        self._anonymous.addoption(*opts, **attrs)

    def parse(self, args):
        from _pytest._argcomplete import try_argcomplete
        self.optparser = self._getparser()
        try_argcomplete(self.optparser)
        return self.optparser.parse_args([str(x) for x in args])

    def _getparser(self):
        from _pytest._argcomplete import filescompleter
        optparser = MyOptionParser(self)
        groups = self._groups + [self._anonymous]
        for group in groups:
            if group.options:
                desc = group.description or group.name
                arggroup = optparser.add_argument_group(desc)
                for option in group.options:
                    n = option.names()
                    a = option.attrs()
                    arggroup.add_argument(*n, **a)
        # bash like autocompletion for dirs (appending '/')
        optparser.add_argument(FILE_OR_DIR, nargs='*').completer=filescompleter
        return optparser

    def parse_setoption(self, args, option):
        parsedoption = self.parse(args)
        for name, value in parsedoption.__dict__.items():
            setattr(option, name, value)
        return getattr(parsedoption, FILE_OR_DIR)

    def parse_known_args(self, args):
        optparser = self._getparser()
        args = [str(x) for x in args]
        return optparser.parse_known_args(args)[0]

    def addini(self, name, help, type=None, default=None):
        """ register an ini-file option.

        :name: name of the ini-variable
        :type: type of the variable, can be ``pathlist``, ``args`` or ``linelist``.
        :default: default value if no ini-file option exists but is queried.

        The value of ini-variables can be retrieved via a call to
        :py:func:`config.getini(name) <_pytest.config.Config.getini>`.
        """
        assert type in (None, "pathlist", "args", "linelist")
        self._inidict[name] = (help, type, default)
        self._ininames.append(name)


class ArgumentError(Exception):
    """
    Raised if an Argument instance is created with invalid or
    inconsistent arguments.
    """

    def __init__(self, msg, option):
        self.msg = msg
        self.option_id = str(option)

    def __str__(self):
        if self.option_id:
            return "option %s: %s" % (self.option_id, self.msg)
        else:
            return self.msg


class Argument:
    """class that mimics the necessary behaviour of optparse.Option """
    _typ_map = {
        'int': int,
        'string': str,
        }
    # enable after some grace period for plugin writers
    TYPE_WARN = False

    def __init__(self, *names, **attrs):
        """store parms in private vars for use in add_argument"""
        self._attrs = attrs
        self._short_opts = []
        self._long_opts = []
        self.dest = attrs.get('dest')
        if self.TYPE_WARN:
            try:
                help = attrs['help']
                if '%default' in help:
                    warnings.warn(
                        'pytest now uses argparse. "%default" should be'
                        ' changed to "%(default)s" ',
                        FutureWarning,
                        stacklevel=3)
            except KeyError:
                pass
        try:
            typ = attrs['type']
        except KeyError:
            pass
        else:
            # this might raise a keyerror as well, don't want to catch that
            if isinstance(typ, py.builtin._basestring):
                if typ == 'choice':
                    if self.TYPE_WARN:
                        warnings.warn(
                            'type argument to addoption() is a string %r.'
                            ' For parsearg this is optional and when supplied '
                            ' should be a type.'
                            ' (options: %s)' % (typ, names),
                            FutureWarning,
                            stacklevel=3)
                    # argparse expects a type here take it from
                    # the type of the first element
                    attrs['type'] = type(attrs['choices'][0])
                else:
                    if self.TYPE_WARN:
                        warnings.warn(
                            'type argument to addoption() is a string %r.'
                            ' For parsearg this should be a type.'
                            ' (options: %s)' % (typ, names),
                            FutureWarning,
                            stacklevel=3)
                    attrs['type'] = Argument._typ_map[typ]
                # used in test_parseopt -> test_parse_defaultgetter
                self.type = attrs['type']
            else:
                self.type = typ
        try:
            # attribute existence is tested in Config._processopt
            self.default = attrs['default']
        except KeyError:
            pass
        self._set_opt_strings(names)
        if not self.dest:
            if self._long_opts:
                self.dest = self._long_opts[0][2:].replace('-', '_')
            else:
                try:
                    self.dest = self._short_opts[0][1:]
                except IndexError:
                    raise ArgumentError(
                        'need a long or short option', self)

    def names(self):
        return self._short_opts + self._long_opts

    def attrs(self):
        # update any attributes set by processopt
        attrs = 'default dest help'.split()
        if self.dest:
            attrs.append(self.dest)
        for attr in attrs:
            try:
                self._attrs[attr] = getattr(self, attr)
            except AttributeError:
                pass
        if self._attrs.get('help'):
            a = self._attrs['help']
            a = a.replace('%default', '%(default)s')
            #a = a.replace('%prog', '%(prog)s')
            self._attrs['help'] = a
        return self._attrs

    def _set_opt_strings(self, opts):
        """directly from optparse

        might not be necessary as this is passed to argparse later on"""
        for opt in opts:
            if len(opt) < 2:
                raise ArgumentError(
                    "invalid option string %r: "
                    "must be at least two characters long" % opt, self)
            elif len(opt) == 2:
                if not (opt[0] == "-" and opt[1] != "-"):
                    raise ArgumentError(
                        "invalid short option string %r: "
                        "must be of the form -x, (x any non-dash char)" % opt,
                        self)
                self._short_opts.append(opt)
            else:
                if not (opt[0:2] == "--" and opt[2] != "-"):
                    raise ArgumentError(
                        "invalid long option string %r: "
                        "must start with --, followed by non-dash" % opt,
                        self)
                self._long_opts.append(opt)

    def __repr__(self):
        retval = 'Argument('
        if self._short_opts:
            retval += '_short_opts: ' + repr(self._short_opts) + ', '
        if self._long_opts:
            retval += '_long_opts: ' + repr(self._long_opts) + ', '
        retval += 'dest: ' + repr(self.dest) + ', '
        if hasattr(self, 'type'):
            retval += 'type: ' + repr(self.type) + ', '
        if hasattr(self, 'default'):
            retval += 'default: ' + repr(self.default) + ', '
        if retval[-2:] == ', ':  # always long enough to test ("Argument(" )
            retval = retval[:-2]
        retval += ')'
        return retval


class OptionGroup:
    def __init__(self, name, description="", parser=None):
        self.name = name
        self.description = description
        self.options = []
        self.parser = parser

    def addoption(self, *optnames, **attrs):
        """ add an option to this group.

        if a shortened version of a long option is specified it will
        be suppressed in the help. addoption('--twowords', '--two-words')
        results in help showing '--two-words' only, but --twowords gets
        accepted **and** the automatic destination is in args.twowords
        """
        option = Argument(*optnames, **attrs)
        self._addoption_instance(option, shortupper=False)

    def _addoption(self, *optnames, **attrs):
        option = Argument(*optnames, **attrs)
        self._addoption_instance(option, shortupper=True)

    def _addoption_instance(self, option, shortupper=False):
        if not shortupper:
            for opt in option._short_opts:
                if opt[0] == '-' and opt[1].islower():
                    raise ValueError("lowercase shortoptions reserved")
        if self.parser:
            self.parser.processoption(option)
        self.options.append(option)


class MyOptionParser(argparse.ArgumentParser):
    def __init__(self, parser):
        self._parser = parser
        argparse.ArgumentParser.__init__(self, usage=parser._usage,
            add_help=False, formatter_class=DropShorterLongHelpFormatter)

    def parse_args(self, args=None, namespace=None):
        """allow splitting of positional arguments"""
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            for arg in argv:
                if arg and arg[0] == '-':
                    msg = argparse._('unrecognized arguments: %s')
                    self.error(msg % ' '.join(argv))
            getattr(args, FILE_OR_DIR).extend(argv)
        return args

class DropShorterLongHelpFormatter(argparse.HelpFormatter):
    """shorten help for long options that differ only in extra hyphens

    - collapse **long** options that are the same except for extra hyphens
    - special action attribute map_long_option allows surpressing additional
      long options
    - shortcut if there are only two options and one of them is a short one
    - cache result on action object as this is called at least 2 times
    """
    def _format_action_invocation(self, action):
        orgstr = argparse.HelpFormatter._format_action_invocation(self, action)
        if orgstr and orgstr[0] != '-': # only optional arguments
            return orgstr
        res = getattr(action, '_formatted_action_invocation', None)
        if res:
            return res
        options = orgstr.split(', ')
        if len(options) == 2 and (len(options[0]) == 2 or len(options[1]) == 2):
            # a shortcut for '-h, --help' or '--abc', '-a'
            action._formatted_action_invocation = orgstr
            return orgstr
        return_list = []
        option_map =  getattr(action, 'map_long_option', {})
        if option_map is None:
            option_map = {}
        short_long = {}
        for option in options:
            if len(option) == 2 or option[2] == ' ':
                continue
            if not option.startswith('--'):
                raise ArgumentError('long optional argument without "--": [%s]'
                                    % (option), self)
            xxoption = option[2:]
            if xxoption.split()[0] not in option_map:
                shortened = xxoption.replace('-', '')
                if shortened not in short_long or \
                   len(short_long[shortened]) < len(xxoption):
                    short_long[shortened] = xxoption
        # now short_long has been filled out to the longest with dashes
        # **and** we keep the right option ordering from add_argument
        for option in options: #
            if len(option) == 2 or option[2] == ' ':
                return_list.append(option)
            if option[2:] == short_long.get(option.replace('-', '')):
                return_list.append(option.replace(' ', '='))
        action._formatted_action_invocation = ', '.join(return_list)
        return action._formatted_action_invocation


class Conftest(object):
    """ the single place for accessing values and interacting
        towards conftest modules from pytest objects.
    """
    def __init__(self, onimport=None):
        self._path2confmods = {}
        self._onimport = onimport
        self._conftestpath2mod = {}
        self._confcutdir = None

    def setinitial(self, namespace):
        """ load initial conftest files given a preparsed "namespace".
            As conftest files may add their own command line options
            which have arguments ('--my-opt somepath') we might get some
            false positives.  All builtin and 3rd party plugins will have
            been loaded, however, so common options will not confuse our logic
            here.
        """
        current = py.path.local()
        self._confcutdir = current.join(namespace.confcutdir, abs=True) \
                                if namespace.confcutdir else None
        testpaths = namespace.file_or_dir
        foundanchor = False
        for path in testpaths:
            path = str(path)
            # remove node-id syntax
            i = path.find("::")
            if i != -1:
                path = path[:i]
            anchor = current.join(path, abs=1)
            if exists(anchor): # we found some file object
                self._try_load_conftest(anchor)
                foundanchor = True
        if not foundanchor:
            self._try_load_conftest(current)

    def _try_load_conftest(self, anchor):
        self.getconftestmodules(anchor)
        # let's also consider test* subdirs
        if anchor.check(dir=1):
            for x in anchor.listdir("test*"):
                if x.check(dir=1):
                    self.getconftestmodules(x)

    def getconftestmodules(self, path):
        try:
            return self._path2confmods[path]
        except KeyError:
            clist = []
            for parent in path.parts():
                if self._confcutdir and self._confcutdir.relto(parent):
                    continue
                conftestpath = parent.join("conftest.py")
                if conftestpath.check(file=1):
                    mod = self.importconftest(conftestpath)
                    clist.append(mod)
            self._path2confmods[path] = clist
            return clist

    def rget_with_confmod(self, name, path):
        modules = self.getconftestmodules(path)
        for mod in reversed(modules):
            try:
                return mod, getattr(mod, name)
            except AttributeError:
                continue
        raise KeyError(name)

    def importconftest(self, conftestpath):
        try:
            return self._conftestpath2mod[conftestpath]
        except KeyError:
            pkgpath = conftestpath.pypkgpath()
            if pkgpath is None:
                _ensure_removed_sysmodule(conftestpath.purebasename)
            try:
                mod = conftestpath.pyimport()
            except Exception:
                raise ConftestImportFailure(conftestpath, sys.exc_info())
            self._conftestpath2mod[conftestpath] = mod
            dirpath = conftestpath.dirpath()
            if dirpath in self._path2confmods:
                for path, mods in self._path2confmods.items():
                    if path and path.relto(dirpath) or path == dirpath:
                        assert mod not in mods
                        mods.append(mod)
            if self._onimport:
                self._onimport(mod)
            return mod


def _ensure_removed_sysmodule(modname):
    try:
        del sys.modules[modname]
    except KeyError:
        pass

class CmdOptions(object):
    """ holds cmdline options as attributes."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        return "<CmdOptions %r>" %(self.__dict__,)

class Notset:
    def __repr__(self):
        return "<NOTSET>"

notset = Notset()
FILE_OR_DIR = 'file_or_dir'
class Config(object):
    """ access to configuration values, pluginmanager and plugin hooks.  """

    def __init__(self, pluginmanager):
        #: access to command line option as attributes.
        #: (deprecated), use :py:func:`getoption() <_pytest.config.Config.getoption>` instead
        self.option = CmdOptions()
        _a = FILE_OR_DIR
        self._parser = Parser(
            usage="%%(prog)s [options] [%s] [%s] [...]" % (_a, _a),
            processopt=self._processopt,
        )
        #: a pluginmanager instance
        self.pluginmanager = pluginmanager
        self.trace = self.pluginmanager.trace.root.get("config")
        self._conftest = Conftest(onimport=self._onimportconftest)
        self.hook = self.pluginmanager.hook
        self._inicache = {}
        self._opt2dest = {}
        self._cleanup = []
        self.pluginmanager.register(self, "pytestconfig")
        self.pluginmanager.set_register_callback(self._register_plugin)
        self._configured = False

    def _register_plugin(self, plugin, name):
        call_plugin = self.pluginmanager.call_plugin
        call_plugin(plugin, "pytest_addhooks",
                    {'pluginmanager': self.pluginmanager})
        self.hook.pytest_plugin_registered(plugin=plugin,
                                           manager=self.pluginmanager)
        dic = call_plugin(plugin, "pytest_namespace", {}) or {}
        if dic:
            import pytest
            setns(pytest, dic)
        call_plugin(plugin, "pytest_addoption", {'parser': self._parser})
        if self._configured:
            call_plugin(plugin, "pytest_configure", {'config': self})

    def do_configure(self):
        assert not self._configured
        self._configured = True
        self.hook.pytest_configure(config=self)

    def do_unconfigure(self):
        assert self._configured
        self._configured = False
        self.hook.pytest_unconfigure(config=self)
        self.pluginmanager.ensure_shutdown()

    def warn(self, code, message):
        """ generate a warning for this test session. """
        self.hook.pytest_logwarning(code=code, message=message,
                                    fslocation=None, nodeid=None)

    def get_terminal_writer(self):
        return self.pluginmanager.getplugin("terminalreporter")._tw

    def pytest_cmdline_parse(self, pluginmanager, args):
        assert self == pluginmanager.config, (self, pluginmanager.config)
        self.parse(args)
        return self

    def pytest_unconfigure(config):
        while config._cleanup:
            fin = config._cleanup.pop()
            fin()

    def notify_exception(self, excinfo, option=None):
        if option and option.fulltrace:
            style = "long"
        else:
            style = "native"
        excrepr = excinfo.getrepr(funcargs=True,
            showlocals=getattr(option, 'showlocals', False),
            style=style,
        )
        res = self.hook.pytest_internalerror(excrepr=excrepr,
                                             excinfo=excinfo)
        if not py.builtin.any(res):
            for line in str(excrepr).split("\n"):
                sys.stderr.write("INTERNALERROR> %s\n" %line)
                sys.stderr.flush()

    def cwd_relative_nodeid(self, nodeid):
        # nodeid's are relative to the rootpath, compute relative to cwd
        if self.invocation_dir != self.rootdir:
            fullpath = self.rootdir.join(nodeid)
            nodeid = self.invocation_dir.bestrelpath(fullpath)
        return nodeid

    @classmethod
    def fromdictargs(cls, option_dict, args):
        """ constructor useable for subprocesses. """
        pluginmanager = get_plugin_manager()
        config = pluginmanager.config
        config._preparse(args, addopts=False)
        config.option.__dict__.update(option_dict)
        for x in config.option.plugins:
            config.pluginmanager.consider_pluginarg(x)
        return config

    def _onimportconftest(self, conftestmodule):
        self.trace("loaded conftestmodule %r" %(conftestmodule,))
        self.pluginmanager.consider_conftest(conftestmodule)

    def _processopt(self, opt):
        for name in opt._short_opts + opt._long_opts:
            self._opt2dest[name] = opt.dest

        if hasattr(opt, 'default') and opt.dest:
            if not hasattr(self.option, opt.dest):
                setattr(self.option, opt.dest, opt.default)

    def _getmatchingplugins(self, fspath):
        return self.pluginmanager._plugins + \
               self._conftest.getconftestmodules(fspath)

    def pytest_load_initial_conftests(self, early_config):
        self._conftest.setinitial(early_config.known_args_namespace)
    pytest_load_initial_conftests.trylast = True

    def _initini(self, args):
        parsed_args = self._parser.parse_known_args(args)
        r = determine_setup(parsed_args.inifilename, parsed_args.file_or_dir)
        self.rootdir, self.inifile, self.inicfg = r
        self.invocation_dir = py.path.local()
        self._parser.addini('addopts', 'extra command line options', 'args')
        self._parser.addini('minversion', 'minimally required pytest version')

    def _preparse(self, args, addopts=True):
        self._initini(args)
        if addopts:
            args[:] = shlex.split(os.environ.get('PYTEST_ADDOPTS', '')) + args
            args[:] = self.getini("addopts") + args
        self._checkversion()
        self.pluginmanager.consider_preparse(args)
        self.pluginmanager.consider_setuptools_entrypoints()
        self.pluginmanager.consider_env()
        self.known_args_namespace = ns = self._parser.parse_known_args(args)
        try:
            self.hook.pytest_load_initial_conftests(early_config=self,
                    args=args, parser=self._parser)
        except ConftestImportFailure:
            e = sys.exc_info()[1]
            if ns.help or ns.version:
                # we don't want to prevent --help/--version to work
                # so just let is pass and print a warning at the end
                self.pluginmanager._warnings.append(
                        "could not load initial conftests (%s)\n" % e.path)
            else:
                raise

    def _checkversion(self):
        import pytest
        minver = self.inicfg.get('minversion', None)
        if minver:
            ver = minver.split(".")
            myver = pytest.__version__.split(".")
            if myver < ver:
                raise pytest.UsageError(
                    "%s:%d: requires pytest-%s, actual pytest-%s'" %(
                    self.inicfg.config.path, self.inicfg.lineof('minversion'),
                    minver, pytest.__version__))

    def parse(self, args):
        # parse given cmdline arguments into this config object.
        assert not hasattr(self, 'args'), (
                "can only parse cmdline args at most once per Config object")
        self._origargs = args
        self._preparse(args)
        # XXX deprecated hook:
        self.hook.pytest_cmdline_preparse(config=self, args=args)
        args = self._parser.parse_setoption(args, self.option)
        if not args:
            args.append(os.getcwd())
        self.args = args

    def addinivalue_line(self, name, line):
        """ add a line to an ini-file option. The option must have been
        declared but might not yet be set in which case the line becomes the
        the first line in its value. """
        x = self.getini(name)
        assert isinstance(x, list)
        x.append(line) # modifies the cached list inline

    def getini(self, name):
        """ return configuration value from an :ref:`ini file <inifiles>`. If the
        specified name hasn't been registered through a prior
        :py:func:`parser.addini <pytest.config.Parser.addini>`
        call (usually from a plugin), a ValueError is raised. """
        try:
            return self._inicache[name]
        except KeyError:
            self._inicache[name] = val = self._getini(name)
            return val

    def _getini(self, name):
        try:
            description, type, default = self._parser._inidict[name]
        except KeyError:
            raise ValueError("unknown configuration value: %r" %(name,))
        try:
            value = self.inicfg[name]
        except KeyError:
            if default is not None:
                return default
            if type is None:
                return ''
            return []
        if type == "pathlist":
            dp = py.path.local(self.inicfg.config.path).dirpath()
            l = []
            for relpath in shlex.split(value):
                l.append(dp.join(relpath, abs=True))
            return l
        elif type == "args":
            return shlex.split(value)
        elif type == "linelist":
            return [t for t in map(lambda x: x.strip(), value.split("\n")) if t]
        else:
            assert type is None
            return value

    def _getconftest_pathlist(self, name, path):
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

    def getoption(self, name, default=notset, skip=False):
        """ return command line option value.

        :arg name: name of the option.  You may also specify
            the literal ``--OPT`` option instead of the "dest" option name.
        :arg default: default value if no option of that name exists.
        :arg skip: if True raise pytest.skip if option does not exists
            or has a None value.
        """
        name = self._opt2dest.get(name, name)
        try:
            val = getattr(self.option, name)
            if val is None and skip:
                raise AttributeError(name)
            return val
        except AttributeError:
            if default is not notset:
                return default
            if skip:
                import pytest
                pytest.skip("no %r option found" %(name,))
            raise ValueError("no option named %r" % (name,))

    def getvalue(self, name, path=None):
        """ (deprecated, use getoption()) """
        return self.getoption(name)

    def getvalueorskip(self, name, path=None):
        """ (deprecated, use getoption(skip=True)) """
        return self.getoption(name, skip=True)

def exists(path, ignore=EnvironmentError):
    try:
        return path.check()
    except ignore:
        return False

def getcfg(args, inibasenames):
    args = [x for x in args if not str(x).startswith("-")]
    if not args:
        args = [py.path.local()]
    for arg in args:
        arg = py.path.local(arg)
        for base in arg.parts(reverse=True):
            for inibasename in inibasenames:
                p = base.join(inibasename)
                if exists(p):
                    iniconfig = py.iniconfig.IniConfig(p)
                    if 'pytest' in iniconfig.sections:
                        return base, p, iniconfig['pytest']
                    elif inibasename == "pytest.ini":
                        # allowed to be empty
                        return base, p, {}
    return None, None, None


def get_common_ancestor(args):
    # args are what we get after early command line parsing (usually
    # strings, but can be py.path.local objects as well)
    common_ancestor = None
    for arg in args:
        if str(arg)[0] == "-":
            continue
        p = py.path.local(arg)
        if common_ancestor is None:
            common_ancestor = p
        else:
            if p.relto(common_ancestor) or p == common_ancestor:
                continue
            elif common_ancestor.relto(p):
                common_ancestor = p
            else:
                shared = p.common(common_ancestor)
                if shared is not None:
                    common_ancestor = shared
    if common_ancestor is None:
        common_ancestor = py.path.local()
    elif not common_ancestor.isdir():
        common_ancestor = common_ancestor.dirpath()
    return common_ancestor


def determine_setup(inifile, args):
    if inifile:
        iniconfig = py.iniconfig.IniConfig(inifile)
        try:
            inicfg = iniconfig["pytest"]
        except KeyError:
            inicfg = None
        rootdir = get_common_ancestor(args)
    else:
        ancestor = get_common_ancestor(args)
        rootdir, inifile, inicfg = getcfg(
            [ancestor], ["pytest.ini", "tox.ini", "setup.cfg"])
        if rootdir is None:
            for rootdir in ancestor.parts(reverse=True):
                if rootdir.join("setup.py").exists():
                    break
            else:
                rootdir = ancestor
    return rootdir, inifile, inicfg or {}


def setns(obj, dic):
    import pytest
    for name, value in dic.items():
        if isinstance(value, dict):
            mod = getattr(obj, name, None)
            if mod is None:
                modname = "pytest.%s" % name
                mod = types.ModuleType(modname)
                sys.modules[modname] = mod
                mod.__all__ = []
                setattr(obj, name, mod)
            obj.__all__.append(name)
            setns(mod, value)
        else:
            setattr(obj, name, value)
            obj.__all__.append(name)
            #if obj != pytest:
            #    pytest.__all__.append(name)
            setattr(pytest, name, value)


def create_terminal_writer(config, *args, **kwargs):
    """Create a TerminalWriter instance configured according to the options
    in the config object. Every code which requires a TerminalWriter object
    and has access to a config object should use this function.
    """
    tw = py.io.TerminalWriter(*args, **kwargs)
    if config.option.color == 'yes':
        tw.hasmarkup = True
    if config.option.color == 'no':
        tw.hasmarkup = False
    return tw
