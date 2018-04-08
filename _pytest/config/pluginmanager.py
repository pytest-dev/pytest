import sys
import os
import types
import warnings
import traceback

import py
import six
from pluggy import PluginManager

import _pytest

from _pytest.outcomes import Skipped
from _pytest.compat import safe_str
from _pytest.config.fs_interaction import exists

default_plugins = (
    "mark main terminal runner python fixtures debugging unittest capture skipping "
    "tmpdir monkeypatch recwarn pastebin helpconfig nose assertion "
    "junitxml resultlog doctest cacheprovider freeze_support "
    "setuponly setupplan warnings logging").split()


builtin_plugins = set(default_plugins)
builtin_plugins.add("pytester")


def _ensure_removed_sysmodule(modname):
    try:
        del sys.modules[modname]
    except KeyError:
        pass


def _get_plugin_specs_as_list(specs):
    """
    Parses a list of "plugin specs" and returns a list of plugin names.

    Plugin specs can be given as a list of strings separated by "," or already as a list/tuple in
    which case it is returned as a list. Specs can also be `None` in which case an
    empty list is returned.
    """
    if specs is not None:
        if isinstance(specs, str):
            specs = specs.split(',') if specs else []
        if not isinstance(specs, (list, tuple)):
            from . import UsageError
            raise UsageError("Plugin specs must be a ','-separated string or a "
                             "list/tuple of strings for plugin names. Given: %r" % specs)
        return list(specs)
    return []


class PytestPluginManager(PluginManager):
    """
    Overwrites :py:class:`pluggy.PluginManager <pluggy.PluginManager>` to add pytest-specific
    functionality:

    * loading plugins from the command line, ``PYTEST_PLUGINS`` env variable and
      ``pytest_plugins`` global variables found in plugins being loaded;
    * ``conftest.py`` loading during start-up;
    """

    def __init__(self):
        super(PytestPluginManager, self).__init__("pytest", implprefix="pytest_")
        self._conftest_plugins = set()

        # state related to local conftest plugins
        self._path2confmods = {}
        self._conftestpath2mod = {}
        self._confcutdir = None
        self._noconftest = False
        self._duplicatepaths = set()

        self.add_hookspecs(_pytest.hookspec)
        self.register(self)
        if os.environ.get('PYTEST_DEBUG'):
            err = sys.stderr
            encoding = getattr(err, 'encoding', 'utf8')
            try:
                err = py.io.dupfile(err, encoding=encoding)
            except Exception:
                pass
            self.trace.root.setwriter(err.write)
            self.enable_tracing()

        # Config._consider_importhook will set a real object if required.
        self.rewrite_hook = _pytest.assertion.DummyRewriteHook()
        # Used to know when we are importing conftests after the pytest_configure stage
        self._configured = False

    def addhooks(self, module_or_class):
        """
        .. deprecated:: 2.8

        Use :py:meth:`pluggy.PluginManager.add_hookspecs <PluginManager.add_hookspecs>`
        instead.
        """
        warning = dict(code="I2",
                       fslocation=_pytest._code.getfslineno(sys._getframe(1)),
                       nodeid=None,
                       message="use pluginmanager.add_hookspecs instead of "
                               "deprecated addhooks() method.")
        self._warn(warning)
        return self.add_hookspecs(module_or_class)

    def parse_hookimpl_opts(self, plugin, name):
        # pytest hooks are always prefixed with pytest_
        # so we avoid accessing possibly non-readable attributes
        # (see issue #1073)
        if not name.startswith("pytest_"):
            return
        # ignore some historic special names which can not be hooks anyway
        if name == "pytest_plugins" or name.startswith("pytest_funcarg__"):
            return

        method = getattr(plugin, name)
        opts = super(PytestPluginManager, self).parse_hookimpl_opts(plugin, name)
        if opts is not None:
            for name in ("tryfirst", "trylast", "optionalhook", "hookwrapper"):
                opts.setdefault(name, hasattr(method, name))
        return opts

    def parse_hookspec_opts(self, module_or_class, name):
        opts = super(PytestPluginManager, self).parse_hookspec_opts(
            module_or_class, name)
        if opts is None:
            method = getattr(module_or_class, name)
            if name.startswith("pytest_"):
                opts = {"firstresult": hasattr(method, "firstresult"),
                        "historic": hasattr(method, "historic")}
        return opts

    def register(self, plugin, name=None):
        if name in ['pytest_catchlog', 'pytest_capturelog']:
            self._warn('{0} plugin has been merged into the core, '
                       'please remove it from your requirements.'.format(
                           name.replace('_', '-')))
            return
        ret = super(PytestPluginManager, self).register(plugin, name)
        if ret:
            self.hook.pytest_plugin_registered.call_historic(
                kwargs=dict(plugin=plugin, manager=self))

            if isinstance(plugin, types.ModuleType):
                self.consider_module(plugin)
        return ret

    def getplugin(self, name):
        # support deprecated naming because plugins (xdist e.g.) use it
        return self.get_plugin(name)

    def hasplugin(self, name):
        """Return True if the plugin with the given name is registered."""
        return bool(self.get_plugin(name))

    def pytest_configure(self, config):
        # XXX now that the pluginmanager exposes hookimpl(tryfirst...)
        # we should remove tryfirst/trylast as markers
        config.addinivalue_line("markers",
                                "tryfirst: mark a hook implementation function such that the "
                                "plugin machinery will try to call it first/as early as possible.")
        config.addinivalue_line("markers",
                                "trylast: mark a hook implementation function such that the "
                                "plugin machinery will try to call it last/as late as possible.")
        self._configured = True

    def _warn(self, message):
        kwargs = message if isinstance(message, dict) else {
            'code': 'I1',
            'message': message,
            'fslocation': None,
            'nodeid': None,
        }
        self.hook.pytest_logwarning.call_historic(kwargs=kwargs)

    #
    # internal API for local conftest plugin handling
    #
    def _set_initial_conftests(self, namespace):
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
        self._noconftest = namespace.noconftest
        testpaths = namespace.file_or_dir
        foundanchor = False
        for path in testpaths:
            path = str(path)
            # remove node-id syntax
            i = path.find("::")
            if i != -1:
                path = path[:i]
            anchor = current.join(path, abs=1)
            if exists(anchor):  # we found some file object
                self._try_load_conftest(anchor)
                foundanchor = True
        if not foundanchor:
            self._try_load_conftest(current)

    def _try_load_conftest(self, anchor):
        self._getconftestmodules(anchor)
        # let's also consider test* subdirs
        if anchor.check(dir=1):
            for x in anchor.listdir("test*"):
                if x.check(dir=1):
                    self._getconftestmodules(x)

    def _getconftestmodules(self, path):
        if self._noconftest:
            return []
        try:
            return self._path2confmods[path]
        except KeyError:
            if path.isfile():
                clist = self._getconftestmodules(path.dirpath())
            else:
                # XXX these days we may rather want to use config.rootdir
                # and allow users to opt into looking into the rootdir parent
                # directories instead of requiring to specify confcutdir
                clist = []
                for parent in path.parts():
                    if self._confcutdir and self._confcutdir.relto(parent):
                        continue
                    conftestpath = parent.join("conftest.py")
                    if conftestpath.isfile():
                        mod = self._importconftest(conftestpath)
                        clist.append(mod)

            self._path2confmods[path] = clist
            return clist

    def _rget_with_confmod(self, name, path):
        modules = self._getconftestmodules(path)
        for mod in reversed(modules):
            try:
                return mod, getattr(mod, name)
            except AttributeError:
                continue
        raise KeyError(name)

    def _importconftest(self, conftestpath):
        try:
            return self._conftestpath2mod[conftestpath]
        except KeyError:
            pkgpath = conftestpath.pypkgpath()
            if pkgpath is None:
                _ensure_removed_sysmodule(conftestpath.purebasename)
            try:
                mod = conftestpath.pyimport()
                if hasattr(mod, 'pytest_plugins') and self._configured:
                    from _pytest.deprecated import PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST
                    warnings.warn(PYTEST_PLUGINS_FROM_NON_TOP_LEVEL_CONFTEST)
            except Exception:
                raise ConftestImportFailure(conftestpath, sys.exc_info())

            self._conftest_plugins.add(mod)
            self._conftestpath2mod[conftestpath] = mod
            dirpath = conftestpath.dirpath()
            if dirpath in self._path2confmods:
                for path, mods in self._path2confmods.items():
                    if path and path.relto(dirpath) or path == dirpath:
                        assert mod not in mods
                        mods.append(mod)
            self.trace("loaded conftestmodule %r" % (mod))
            self.consider_conftest(mod)
            return mod

    #
    # API for bootstrapping plugin loading
    #
    #

    def consider_preparse(self, args):
        for opt1, opt2 in zip(args, args[1:]):
            if opt1 == "-p":
                self.consider_pluginarg(opt2)

    def consider_pluginarg(self, arg):
        if arg.startswith("no:"):
            name = arg[3:]
            self.set_blocked(name)
            if not name.startswith("pytest_"):
                self.set_blocked("pytest_" + name)
        else:
            self.import_plugin(arg)

    def consider_conftest(self, conftestmodule):
        self.register(conftestmodule, name=conftestmodule.__file__)

    def consider_env(self):
        self._import_plugin_specs(os.environ.get("PYTEST_PLUGINS"))

    def consider_module(self, mod):
        self._import_plugin_specs(getattr(mod, 'pytest_plugins', []))

    def _import_plugin_specs(self, spec):
        plugins = _get_plugin_specs_as_list(spec)
        for import_spec in plugins:
            self.import_plugin(import_spec)

    def import_plugin(self, modname):
        # most often modname refers to builtin modules, e.g. "pytester",
        # "terminal" or "capture".  Those plugins are registered under their
        # basename for historic purposes but must be imported with the
        # _pytest prefix.
        assert isinstance(modname, (six.text_type, str)), "module name as text required, got %r" % modname
        modname = str(modname)
        if self.is_blocked(modname) or self.get_plugin(modname) is not None:
            return
        if modname in builtin_plugins:
            importspec = "_pytest." + modname
        else:
            importspec = modname
        self.rewrite_hook.mark_rewrite(importspec)
        try:
            __import__(importspec)
        except ImportError as e:
            new_exc_type = ImportError
            new_exc_message = 'Error importing plugin "%s": %s' % (modname, safe_str(e.args[0]))
            new_exc = new_exc_type(new_exc_message)

            six.reraise(new_exc_type, new_exc, sys.exc_info()[2])

        except Skipped as e:
            self._warn("skipped plugin %r: %s" % ((modname, e.msg)))
        else:
            mod = sys.modules[importspec]
            self.register(mod, modname)


class ConftestImportFailure(Exception):
    def __init__(self, path, excinfo):
        Exception.__init__(self, path, excinfo)
        self.path = path
        self.excinfo = excinfo

    def __str__(self):
        etype, evalue, etb = self.excinfo
        formatted = traceback.format_tb(etb)
        # The level of the tracebacks we want to print is hand crafted :(
        return repr(evalue) + '\n' + ''.join(formatted[2:])
