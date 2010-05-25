""" provide version info, conftest/environment config names. 
"""
import py
import inspect, sys

def pytest_addoption(parser):
    group = parser.getgroup('debugconfig')
    group.addoption('--version', action="store_true", 
            help="display py lib version and import information.")
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
    group.addoption("--help-config", action="store_true", dest="helpconfig", 
            help="show available conftest.py and ENV-variable names.")


def pytest_configure(__multicall__, config):
    if config.option.version:
        p = py.path.local(py.__file__).dirpath()
        sys.stderr.write("This is py.test version %s, imported from %s\n" % 
            (py.__version__, p))
        sys.exit(0)
    if not config.option.helpconfig:
        return
    __multicall__.execute()
    options = []
    for group in config._parser._groups:
        options.extend(group.options)
    widths = [0] * 10 
    tw = py.io.TerminalWriter()
    tw.sep("-")
    tw.line("%-13s | %-18s | %-25s | %s" %(
            "cmdline name", "conftest.py name", "ENV-variable name", "help"))
    tw.sep("-")

    options = [opt for opt in options if opt._long_opts]
    options.sort(key=lambda x: x._long_opts)
    for opt in options:
        if not opt._long_opts or not opt.dest:
            continue
        optstrings = list(opt._long_opts) # + list(opt._short_opts)
        optstrings = filter(None, optstrings)
        optstring = "|".join(optstrings)
        line = "%-13s | %-18s | %-25s | %s" %(
            optstring, 
            "option_%s" % opt.dest, 
            "PYTEST_OPTION_%s" % opt.dest.upper(),
            opt.help and opt.help or "", 
            )
        tw.line(line[:tw.fullwidth])
    for name, help in conftest_options:
        line = "%-13s | %-18s | %-25s | %s" %(
            "", 
            name, 
            "",
            help, 
            )
        tw.line(line[:tw.fullwidth])
        
    tw.sep("-")
    sys.exit(0)

conftest_options = (
    ('pytest_plugins', 'list of plugin names to load'),
    ('collect_ignore', '(relative) paths ignored during collection'), 
    ('rsyncdirs', 'to-be-rsynced directories for dist-testing'), 
)

def pytest_report_header(config):
    lines = []
    if config.option.debug or config.option.traceconfig:
        lines.append("using py lib: %s" % (py.path.local(py.__file__).dirpath()))
    if config.option.traceconfig:
        lines.append("active plugins:")
        plugins = []
        items = config.pluginmanager._name2plugin.items()
        for name, plugin in items:
            lines.append("    %-20s: %s" %(name, repr(plugin)))
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
            method_args = getargs(method)
            #print "method_args", method_args
            if '__multicall__' in method_args:
                method_args.remove('__multicall__')
            hook = hooks[name]
            hookargs = getargs(hook)
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
            raise PluginValidationError("%s:\n%s" %(name, stringio.getvalue()))

class PluginValidationError(Exception):
    """ plugin failed validation. """

def isgenerichook(name):
    return name == "pytest_plugins" or \
           name.startswith("pytest_funcarg__")

def getargs(func):
    args = inspect.getargs(py.code.getrawcode(func))[0]
    startindex = inspect.ismethod(func) and 1 or 0
    return args[startindex:]

def collectattr(obj, prefixes=("pytest_",)):
    methods = {}
    for apiname in dir(obj):
        for prefix in prefixes:
            if apiname.startswith(prefix):
                methods[apiname] = getattr(obj, apiname) 
    return methods 

def formatdef(func):
    return "%s%s" %(
        func.__name__, 
        inspect.formatargspec(*inspect.getargspec(func))
    )

