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

here = py.magic.autopath().dirpath()

option = py.test.config.addoptions("execnet options",
        Option('-S', '',
               action="store", dest="sshtarget", default=None,
               help=("target to run tests requiring ssh, e.g. "
                     "user@codespeak.net")),
        Option('', '--apigenpath',
               action="store", dest="apigenpath",
               default=here.join("../apigen").strpath,
               type="string",
               help="absolute path to where apigen docs are built"),
        Option('', '--docpath',
               action='store', dest='docpath',
               default=here.join('doc').strpath, type='string',
               help='absolute path to where the docs are built'),
    )

dist_rsync_roots = ['.']
