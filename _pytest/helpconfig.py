""" version info, help messages, tracing configuration.  """
import py
import pytest
import inspect, sys
from _pytest.core import varnames

def pytest_addoption(parser):
    group = parser.getgroup('debugconfig')
    group.addoption('--version', action="store_true",
            help="display pytest lib version and import information.")
    group._addoption("-h", "--help", action="store_true", dest="help",
            help="show help message and configuration info")
    group._addoption('-p', action="append", dest="plugins", default = [],
               metavar="name",
               help="early-load given plugin (multi-allowed).")
    group.addoption('--traceconfig',
               action="store_true", dest="traceconfig", default=False,
               help="trace considerations of conftest.py files."),
    group._addoption('--nomagic',
               action="store_true", dest="nomagic", default=False,
               help="don't reinterpret asserts, no traceback cutting. ")
    group.addoption('--debug',
               action="store_true", dest="debug", default=False,
               help="generate and show internal debugging information.")


def pytest_cmdline_main(config):
    if config.option.version:
        p = py.path.local(pytest.__file__)
        sys.stderr.write("This is py.test version %s, imported from %s\n" %
            (pytest.__version__, p))
        plugininfo = getpluginversioninfo(config)
        if plugininfo:
            for line in plugininfo:
                sys.stderr.write(line + "\n")
        return 0
    elif config.option.help:
        config.pluginmanager.do_configure(config)
        showhelp(config)
        return 0

def showhelp(config):
    tw = py.io.TerminalWriter()
    tw.write(config._parser.optparser.format_help())
    tw.line()
    tw.line()
    #tw.sep( "=", "config file settings")
    tw.line("[pytest] ini-options in the next "
            "pytest.ini|tox.ini|setup.cfg file:")
    tw.line()

    for name in config._parser._ininames:
        help, type, default = config._parser._inidict[name]
        if type is None:
            type = "string"
        spec = "%s (%s)" % (name, type)
        line = "  %-24s %s" %(spec, help)
        tw.line(line[:tw.fullwidth])

    tw.line() ; tw.line()
    #tw.sep("=")
    return

    tw.line("conftest.py options:")
    tw.line()
    conftestitems = sorted(config._parser._conftestdict.items())
    for name, help in conftest_options + conftestitems:
        line = "   %-15s  %s" %(name, help)
        tw.line(line[:tw.fullwidth])
    tw.line()
    #tw.sep( "=")

conftest_options = [
    ('pytest_plugins', 'list of plugin names to load'),
]

def getpluginversioninfo(config):
    lines = []
    plugininfo = config.pluginmanager._plugin_distinfo
    if plugininfo:
        lines.append("setuptools registered plugins:")
        for dist, plugin in plugininfo:
            loc = getattr(plugin, '__file__', repr(plugin))
            content = "%s-%s at %s" % (dist.project_name, dist.version, loc)
            lines.append("  " + content)
    return lines

def pytest_report_header(config):
    lines = []
    if config.option.debug or config.option.traceconfig:
        lines.append("using: pytest-%s pylib-%s" %
            (pytest.__version__,py.__version__))

        verinfo = getpluginversioninfo(config)
        if verinfo:
            lines.extend(verinfo)
            
    if config.option.traceconfig:
        lines.append("active plugins:")
        plugins = []
        items = config.pluginmanager._name2plugin.items()
        for name, plugin in items:
            if hasattr(plugin, '__file__'):
                r = plugin.__file__
            else:
                r = repr(plugin)
            lines.append("    %-20s: %s" %(name, r))
    return lines


# =====================================================
# validate plugin syntax and hooks
# =====================================================

def pytest_plugin_registered(manager, plugin):
    methods = collectattr(plugin)
    hooks = {}
    for hookspec in manager.hook._hookspecs:
        hooks.update(collectattr(hookspec))

    stringio = py.io.TextIO()
    def Print(*args):
        if args:
            stringio.write(" ".join(map(str, args)))
        stringio.write("\n")

    fail = False
    while methods:
        name, method = methods.popitem()
        #print "checking", name
        if isgenerichook(name):
            continue
        if name not in hooks:
            if not getattr(method, 'optionalhook', False):
                Print("found unknown hook:", name)
                fail = True
        else:
            #print "checking", method
            method_args = list(varnames(method))
            if '__multicall__' in method_args:
                method_args.remove('__multicall__')
            hook = hooks[name]
            hookargs = varnames(hook)
            for arg in method_args:
                if arg not in hookargs:
                    Print("argument %r not available"  %(arg, ))
                    Print("actual definition: %s" %(formatdef(method)))
                    Print("available hook arguments: %s" %
                            ", ".join(hookargs))
                    fail = True
                    break
            #if not fail:
            #    print "matching hook:", formatdef(method)
        if fail:
            name = getattr(plugin, '__name__', plugin)
            raise PluginValidationError("%s:\n%s" % (name, stringio.getvalue()))

class PluginValidationError(Exception):
    """ plugin failed validation. """

def isgenerichook(name):
    return name == "pytest_plugins" or \
           name.startswith("pytest_funcarg__")

def collectattr(obj):
    methods = {}
    for apiname in dir(obj):
        if apiname.startswith("pytest_"):
            methods[apiname] = getattr(obj, apiname)
    return methods

def formatdef(func):
    return "%s%s" % (
        func.__name__,
        inspect.formatargspec(*inspect.getargspec(func))
    )

