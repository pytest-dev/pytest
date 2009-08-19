""" provide version info, conftest/environment config names. 
"""
import py
import sys

def pytest_addoption(parser):
    group = parser.getgroup('debugconfig')
    group.addoption("--help-config", action="store_true", dest="helpconfig", 
            help="show available conftest.py and ENV-variable names.")
    group.addoption('--version', action="store_true", 
            help="display py lib version and import information.")

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
    options.sort(lambda x, y: cmp(x._long_opts, y._long_opts))
    for opt in options:
        if not opt._long_opts:
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
