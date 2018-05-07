""" command line options, ini-file and conftest.py processing. """
from __future__ import absolute_import, division, print_function
import argparse
import shlex
import traceback
import copy
import six
import py
# DON't import pytest here because it causes import cycle troubles
import sys
import os

import _pytest._code
import _pytest.hookspec  # the extension point definitions
import _pytest.assertion
from pluggy import HookimplMarker, HookspecMarker


from .fs_interaction import determine_setup
hookimpl = HookimplMarker("pytest")
hookspec = HookspecMarker("pytest")

# pytest startup
#


def main(args=None, plugins=None):
    """ return exit code, after performing an in-process test run.

    :arg args: list of command line arguments.

    :arg plugins: list of plugin objects to be auto-registered during
                  initialization.
    """
    try:
        config = get_config()
        from .pluginmanager import ConftestImportFailure
        try:
            config = _prepareconfig(config, args, plugins)
        except ConftestImportFailure as e:
            tw = py.io.TerminalWriter(sys.stderr)
            for line in traceback.format_exception(*e.excinfo):
                tw.line(line.rstrip(), red=True)
            tw.line("ERROR: could not load %s\n" % (e.path,), red=True)
            return 4
        else:
            try:
                return config.hook.pytest_cmdline_main(config=config)
            finally:
                config._ensure_unconfigure()
    except UsageError as e:
        tw = py.io.TerminalWriter(sys.stderr)
        for msg in e.args:
            tw.line("ERROR: {}\n".format(msg), red=True)
        return 4


class cmdline(object):  # NOQA compatibility namespace
    main = staticmethod(main)


class UsageError(Exception):
    """ error in pytest usage or invocation"""


class PrintHelp(Exception):
    """Raised when pytest should print it's help to skip the rest of the
    argument parsing and validation."""
    pass


def filename_arg(path, optname):
    """ Argparse type validator for filename arguments.

    :path: path of filename
    :optname: name of the option
    """
    if os.path.isdir(path):
        raise UsageError("{0} must be a filename, given: {1}".format(optname, path))
    return path


def directory_arg(path, optname):
    """Argparse type validator for directory arguments.

    :path: path of directory
    :optname: name of the option
    """
    if not os.path.isdir(path):
        raise UsageError("{0} must be a directory, given: {1}".format(optname, path))
    return path


def get_config():
    # subsequent calls to main will create a fresh instance
    from .pluginmanager import PytestPluginManager, default_plugins
    pluginmanager = PytestPluginManager()
    config = Config(pluginmanager)
    for spec in default_plugins:
        pluginmanager.import_plugin(spec)
    return config


def get_plugin_manager():
    """
    Obtain a new instance of the
    :py:class:`_pytest.config.PytestPluginManager`, with default plugins
    already loaded.

    This function can be used by integration with other tools, like hooking
    into pytest to run tests into an IDE.
    """
    return get_config().pluginmanager


def _prepareconfig(config, args=None, plugins=None):
    warning = None
    if args is None:
        args = sys.argv[1:]
    elif isinstance(args, py.path.local):
        args = [str(args)]
    elif not isinstance(args, (tuple, list)):
        if not isinstance(args, str):
            raise ValueError("not a string or argument list: %r" % (args,))
        args = shlex.split(args, posix=sys.platform != "win32")
        from _pytest import deprecated
        warning = deprecated.MAIN_STR_ARGS
    pluginmanager = config.pluginmanager
    try:
        if plugins:
            for plugin in plugins:
                if isinstance(plugin, six.string_types):
                    pluginmanager.consider_pluginarg(plugin)
                else:
                    pluginmanager.register(plugin)
        if warning:
            config.warn('C1', warning)
        return pluginmanager.hook.pytest_cmdline_parse(
            pluginmanager=pluginmanager, args=args)
    except BaseException:
        config._ensure_unconfigure()
        raise


class Notset(object):
    def __repr__(self):
        return "<NOTSET>"


notset = Notset()


def _iter_rewritable_modules(package_files):
    for fn in package_files:
        is_simple_module = '/' not in fn and fn.endswith('.py')
        is_package = fn.count('/') == 1 and fn.endswith('__init__.py')
        if is_simple_module:
            module_name, _ = os.path.splitext(fn)
            yield module_name
        elif is_package:
            package_name = os.path.dirname(fn)
            yield package_name


class Config(object):
    """ access to configuration values, pluginmanager and plugin hooks.  """

    def __init__(self, pluginmanager):
        #: access to command line option as attributes.
        #: (deprecated), use :py:func:`getoption() <_pytest.config.Config.getoption>` instead
        self.option = argparse.Namespace()
        from .argument_parsing import FILE_OR_DIR, Parser
        _a = FILE_OR_DIR
        self._parser = Parser(
            usage="%%(prog)s [options] [%s] [%s] [...]" % (_a, _a),
            processopt=self._processopt,
        )
        #: a pluginmanager instance
        self.pluginmanager = pluginmanager
        self.trace = self.pluginmanager.trace.root.get("config")
        self.hook = self.pluginmanager.hook
        self._inicache = {}
        self._override_ini = ()
        self._opt2dest = {}
        self._cleanup = []
        self._warn = self.pluginmanager._warn
        self.pluginmanager.register(self, "pytestconfig")

        self._configured = False

        self.hook.pytest_addoption.call_historic(kwargs=dict(parser=self._parser))

    def add_cleanup(self, func):
        """ Add a function to be called when the config object gets out of
        use (usually coninciding with pytest_unconfigure)."""
        self._cleanup.append(func)

    def _do_configure(self):
        assert not self._configured
        self._configured = True
        self.hook.pytest_configure.call_historic(kwargs=dict(config=self))

    def _ensure_unconfigure(self):
        if self._configured:
            self._configured = False
            self.hook.pytest_unconfigure(config=self)
            self.hook.pytest_configure._call_history = []
        while self._cleanup:
            fin = self._cleanup.pop()
            fin()

    def warn(self, code, message, fslocation=None, nodeid=None):
        """ generate a warning for this test session. """
        self.hook.pytest_logwarning.call_historic(kwargs=dict(
            code=code, message=message,
            fslocation=fslocation, nodeid=nodeid))

    def get_terminal_writer(self):
        return self.pluginmanager.get_plugin("terminalreporter")._tw

    def pytest_cmdline_parse(self, pluginmanager, args):
        # REF1 assert self == pluginmanager.config, (self, pluginmanager.config)
        self.parse(args)
        return self

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
        if not any(res):
            for line in str(excrepr).split("\n"):
                sys.stderr.write("INTERNALERROR> %s\n" % line)
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
        config = get_config()
        config.option.__dict__.update(option_dict)
        config.parse(args, addopts=False)
        for x in config.option.plugins:
            config.pluginmanager.consider_pluginarg(x)
        return config

    def _processopt(self, opt):
        for name in opt._short_opts + opt._long_opts:
            self._opt2dest[name] = opt.dest

        if hasattr(opt, 'default') and opt.dest:
            if not hasattr(self.option, opt.dest):
                setattr(self.option, opt.dest, opt.default)

    @hookimpl(trylast=True)
    def pytest_load_initial_conftests(self, early_config):
        self.pluginmanager._set_initial_conftests(early_config.known_args_namespace)

    def _initini(self, args):
        ns, unknown_args = self._parser.parse_known_and_unknown_args(args, namespace=copy.copy(self.option))
        r = determine_setup(ns.inifilename, ns.file_or_dir + unknown_args, warnfunc=self.warn,
                            rootdir_cmd_arg=ns.rootdir or None)
        self.rootdir, self.inifile, self.inicfg = r
        self._parser.extra_info['rootdir'] = self.rootdir
        self._parser.extra_info['inifile'] = self.inifile
        self.invocation_dir = py.path.local()
        self._parser.addini('addopts', 'extra command line options', 'args')
        self._parser.addini('minversion', 'minimally required pytest version')
        self._override_ini = ns.override_ini or ()

    def _consider_importhook(self, args):
        """Install the PEP 302 import hook if using assertion rewriting.

        Needs to parse the --assert=<mode> option from the commandline
        and find all the installed plugins to mark them for rewriting
        by the importhook.
        """
        ns, unknown_args = self._parser.parse_known_and_unknown_args(args)
        mode = ns.assertmode
        if mode == 'rewrite':
            try:
                hook = _pytest.assertion.install_importhook(self)
            except SystemError:
                mode = 'plain'
            else:
                self._mark_plugins_for_rewrite(hook)
        _warn_about_missing_assertion(mode)

    def _mark_plugins_for_rewrite(self, hook):
        """
        Given an importhook, mark for rewrite any top-level
        modules or packages in the distribution package for
        all pytest plugins.
        """
        import pkg_resources
        self.pluginmanager.rewrite_hook = hook

        # 'RECORD' available for plugins installed normally (pip install)
        # 'SOURCES.txt' available for plugins installed in dev mode (pip install -e)
        # for installed plugins 'SOURCES.txt' returns an empty list, and vice-versa
        # so it shouldn't be an issue
        metadata_files = 'RECORD', 'SOURCES.txt'

        package_files = (
            entry.split(',')[0]
            for entrypoint in pkg_resources.iter_entry_points('pytest11')
            for metadata in metadata_files
            for entry in entrypoint.dist._get_metadata(metadata)
        )

        for name in _iter_rewritable_modules(package_files):
            hook.mark_rewrite(name)

    def _preparse(self, args, addopts=True):
        if addopts:
            args[:] = shlex.split(os.environ.get('PYTEST_ADDOPTS', '')) + args
        self._initini(args)
        if addopts:
            args[:] = self.getini("addopts") + args
        self._checkversion()
        self._consider_importhook(args)
        self.pluginmanager.consider_preparse(args)
        self.pluginmanager.load_setuptools_entrypoints('pytest11')
        self.pluginmanager.consider_env()
        self.known_args_namespace = ns = self._parser.parse_known_args(
            args, namespace=copy.copy(self.option))
        if self.known_args_namespace.confcutdir is None and self.inifile:
            confcutdir = py.path.local(self.inifile).dirname
            self.known_args_namespace.confcutdir = confcutdir

        from .pluginmanager import ConftestImportFailure
        try:
            self.hook.pytest_load_initial_conftests(early_config=self,
                                                    args=args, parser=self._parser)
        except ConftestImportFailure:
            e = sys.exc_info()[1]
            if ns.help or ns.version:
                # we don't want to prevent --help/--version to work
                # so just let is pass and print a warning at the end
                self._warn("could not load initial conftests (%s)\n" % e.path)
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
                    "%s:%d: requires pytest-%s, actual pytest-%s'" % (
                        self.inicfg.config.path, self.inicfg.lineof('minversion'),
                        minver, pytest.__version__))

    def parse(self, args, addopts=True):
        # parse given cmdline arguments into this config object.
        assert not hasattr(self, 'args'), (
            "can only parse cmdline args at most once per Config object")
        self._origargs = args
        self.hook.pytest_addhooks.call_historic(
            kwargs=dict(pluginmanager=self.pluginmanager))
        self._preparse(args, addopts=addopts)
        # XXX deprecated hook:
        self.hook.pytest_cmdline_preparse(config=self, args=args)
        self._parser.after_preparse = True
        try:
            args = self._parser.parse_setoption(args, self.option, namespace=self.option)
            if not args:
                cwd = os.getcwd()
                if cwd == self.rootdir:
                    args = self.getini('testpaths')
                if not args:
                    args = [cwd]
            self.args = args
        except PrintHelp:
            pass

    def addinivalue_line(self, name, line):
        """ add a line to an ini-file option. The option must have been
        declared but might not yet be set in which case the line becomes the
        the first line in its value. """
        x = self.getini(name)
        assert isinstance(x, list)
        x.append(line)  # modifies the cached list inline

    def getini(self, name):
        """ return configuration value from an :ref:`ini file <inifiles>`. If the
        specified name hasn't been registered through a prior
        :py:func:`parser.addini <_pytest.config.Parser.addini>`
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
            raise ValueError("unknown configuration value: %r" % (name,))
        value = self._get_override_ini_value(name)
        if value is None:
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
            values = []
            for relpath in shlex.split(value):
                values.append(dp.join(relpath, abs=True))
            return values
        elif type == "args":
            return shlex.split(value)
        elif type == "linelist":
            return [t for t in map(lambda x: x.strip(), value.split("\n")) if t]
        elif type == "bool":
            return bool(_strtobool(value.strip()))
        else:
            assert type is None
            return value

    def _getconftest_pathlist(self, name, path):
        try:
            mod, relroots = self.pluginmanager._rget_with_confmod(name, path)
        except KeyError:
            return None
        modpath = py.path.local(mod.__file__).dirpath()
        values = []
        for relroot in relroots:
            if not isinstance(relroot, py.path.local):
                relroot = relroot.replace("/", py.path.local.sep)
                relroot = modpath.join(relroot, abs=True)
            values.append(relroot)
        return values

    def _get_override_ini_value(self, name):
        value = None
        # override_ini is a list of "ini=value" options
        # always use the last item if multiple values are set for same ini-name,
        # e.g. -o foo=bar1 -o foo=bar2 will set foo to bar2
        for ini_config in self._override_ini:
            try:
                key, user_ini_value = ini_config.split("=", 1)
            except ValueError:
                raise UsageError("-o/--override-ini expects option=value style.")
            else:
                if key == name:
                    value = user_ini_value
        return value

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
                pytest.skip("no %r option found" % (name,))
            raise ValueError("no option named %r" % (name,))

    def getvalue(self, name, path=None):
        """ (deprecated, use getoption()) """
        return self.getoption(name)

    def getvalueorskip(self, name, path=None):
        """ (deprecated, use getoption(skip=True)) """
        return self.getoption(name, skip=True)


def _assertion_supported():
    try:
        assert False
    except AssertionError:
        return True
    else:
        return False


def _warn_about_missing_assertion(mode):
    if not _assertion_supported():
        if mode == 'plain':
            sys.stderr.write("WARNING: ASSERTIONS ARE NOT EXECUTED"
                             " and FAILING TESTS WILL PASS.  Are you"
                             " using python -O?")
        else:
            sys.stderr.write("WARNING: assertions not in test modules or"
                             " plugins will be ignored"
                             " because assert statements are not executed "
                             "by the underlying Python interpreter "
                             "(are you using python -O?)\n")


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


def _strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.

    .. note:: copied from distutils.util
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))
