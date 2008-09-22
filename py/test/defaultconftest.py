import py

Module = py.test.collect.Module
DoctestFile = py.test.collect.DoctestFile
Directory = py.test.collect.Directory
Class = py.test.collect.Class
Generator = py.test.collect.Generator
Function = py.test.collect.Function
Instance = py.test.collect.Instance

conf_iocapture = "fd" # overridable from conftest.py 

# ===================================================
# Distributed testing specific options 

#dist_hosts: needs to be provided by user
#dist_rsync_roots: might be provided by user, if not present or None,
#                  whole pkgdir will be rsynced
# XXX deprecated dist_remotepython = None
dist_taskspernode = 15
dist_boxed = False
if hasattr(py.std.os, 'nice'):
    dist_nicelevel = py.std.os.nice(0) # nice py.test works
else:
    dist_nicelevel = 0
dist_rsync_ignore = []

# ===================================================

def adddefaultoptions(config):
    Option = config.Option 
    config._addoptions('general options',
        Option('-v', '--verbose',
               action="count", dest="verbose", default=0,
               help="increase verbosity."),
        Option('-x', '--exitfirst',
               action="store_true", dest="exitfirst", default=False,
               help="exit instantly on first error or failed test."),
        Option('-s', '--nocapture',
               action="store_true", dest="nocapture", default=False,
               help="disable catching of sys.stdout/stderr output."),
        Option('-k',
               action="store", dest="keyword", default='',
               help="only run test items matching the given "
                    "keyword expression."),
        Option('-l', '--showlocals',
               action="store_true", dest="showlocals", default=False,
               help="show locals in tracebacks (disabled by default)."),
        Option('--showskipsummary',
               action="store_true", dest="showskipsummary", default=False,
               help="always show summary of skipped tests"), 
        Option('', '--pdb',
               action="store_true", dest="usepdb", default=False,
               help="start pdb (the Python debugger) on errors."),
        Option('', '--eventlog',
               action="store", dest="eventlog", default=None,
               help="write reporting events to given file."),
        Option('', '--tracedir',
               action="store", dest="tracedir", default=None,
               help="write tracing information to the given directory."),
        Option('', '--tb',
               action="store", dest="tbstyle", default='long',
               type="choice", choices=['long', 'short', 'no'],
               help="traceback verboseness (long/short/no)."),
        Option('', '--fulltrace',
               action="store_true", dest="fulltrace", default=False,
               help="don't cut any tracebacks (default is to cut)."),
        Option('', '--nomagic',
               action="store_true", dest="nomagic", default=False,
               help="refrain from using magic as much as possible."),
        Option('', '--collectonly',
               action="store_true", dest="collectonly", default=False,
               help="only collect tests, don't execute them."),
        Option('', '--traceconfig',
               action="store_true", dest="traceconfig", default=False,
               help="trace considerations of conftest.py files."),
        Option('-f', '--looponfailing',
               action="store_true", dest="looponfailing", default=False,
               help="loop on failing test set."),
        Option('', '--exec',
               action="store", dest="executable", default=None,
               help="python executable to run the tests with."),
        Option('-n', '--numprocesses', dest="numprocesses", default=0, 
               action="store", type="int", 
               help="number of local test processes."),
        Option('', '--debug',
               action="store_true", dest="debug", default=False,
               help="turn on debugging information."),
    )

    config._addoptions('EXPERIMENTAL options',
        Option('-d', '--dist',
               action="store_true", dest="dist", default=False,
               help="ad-hoc distribute tests across machines (requires conftest settings)"), 
        Option('-w', '--startserver',
               action="store_true", dest="startserver", default=False,
               help="starts local web server for displaying test progress.", 
               ),
        Option('-r', '--runbrowser',
               action="store_true", dest="runbrowser", default=False,
               help="run browser (implies --startserver)."
               ),
        Option('', '--boxed',
               action="store_true", dest="boxed", default=False,
               help="box each test run in a separate process"), 
        Option('', '--rest',
               action='store_true', dest="restreport", default=False,
               help="restructured text output reporting."),
        Option('', '--apigen',
               action="store", dest="apigen",
               help="generate api documentation while testing (requires "
               "argument pointing to a script)."),
        Option('', '--session',
               action="store", dest="session", default=None,
               help="lookup given sessioname in conftest.py files and use it."),
        Option('--resultlog', action="store",
               default=None, dest="resultlog",
               help="path for machine-readable result log")        
    )
