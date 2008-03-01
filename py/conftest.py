#pythonexecutables = ('python2.2', 'python2.3',)
#pythonexecutable = 'python2.2'

# in the future we want to be able to say here:
#def setup_module(extpy):
#    mod = extpy.resolve()
#    mod.module = 23
#    directory = pypath.root.dirpath()

# default values for options (modified from cmdline)
verbose = 0
nocapture = False
collectonly = False
exitfirst = False
fulltrace = False
showlocals = False
nomagic = False

import py
Option = py.test.config.Option

option = py.test.config.addoptions("execnet options",
        Option('-S', '',
               action="store", dest="sshtarget", default=None,
               help=("target to run tests requiring ssh, e.g. "
                     "user@codespeak.net")),
        Option('', '--apigenpath',
               action="store", dest="apigenpath",
               default="../apigen", 
               type="string",
               help="relative path to apigen doc output location (relative from py/)"), 
        Option('', '--docpath',
               action='store', dest='docpath',
               default="doc", type='string',
               help="relative path to doc output location (relative from py/)"), 
        Option('', '--runslowtests',
               action="store_true", dest="runslowtests", default=False,
               help="run slow tests)"),
    )

dist_rsync_roots = ['.']
