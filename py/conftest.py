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
dist_rsync_roots = ['.']
