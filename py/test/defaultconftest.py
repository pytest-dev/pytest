import py

Module = py.test.collect.Module
DoctestFile = py.test.collect.DoctestFile
Directory = py.test.collect.Directory
Class = py.test.collect.Class
Generator = py.test.collect.Generator
Function = py.test.Function
Instance = py.test.collect.Instance

additionalinfo = None

Option = py.test.config.Option

sessionimportpaths = {
    'RSession': 'py.__.test.rsession.rsession', 
    'LSession': 'py.__.test.rsession.rsession', 
    'TerminalSession': 'py.__.test.terminal.terminal', 
    'TkinterSession': 'py.__.test.tkinter.reportsession', 
}

def adddefaultoptions():
    py.test.config.addoptions('general options',
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
               help="only run test items matching the given (google-style) "
                    "keyword expression."),
        Option('-l', '--showlocals',
               action="store_true", dest="showlocals", default=False,
               help="show locals in tracebacks (disabled by default)."),
        Option('', '--pdb',
               action="store_true", dest="usepdb", default=False,
               help="start pdb (the Python debugger) on errors."),
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
        Option('', '--apigen',
               action="store", dest="apigen",
               help="generate api documentation while testing (requires"
               "argument pointing to a script)."),
    )

    py.test.config.addoptions('test-session related options',
        Option('', '--tkinter',
               action="store_true", dest="tkinter", default=False,
               help="use tkinter test session frontend."),
        Option('', '--looponfailing',
               action="store_true", dest="looponfailing", default=False,
               help="loop on failing test set."),
        Option('', '--session',
               action="store", dest="session", default=None,
               help="use given sessionclass, default is terminal."),
        Option('', '--exec',
               action="store", dest="executable", default=None,
               help="python executable to run the tests with."),
        Option('-w', '--startserver',
               action="store_true", dest="startserver", default=False,
               help="start HTTP server listening on localhost:8000 for test."
               ),
        Option('', '--runbrowser',
               action="store_true", dest="runbrowser", default=False,
               help="run browser to point to your freshly started web server."
               ),
        Option('-r', '--rest',
               action='store_true', dest="restreport", default=False,
               help="restructured text output reporting."),
    )
    
