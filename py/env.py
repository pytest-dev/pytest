#!/usr/bin/env python

import sys, os, os.path

progpath = sys.argv[0]
packagedir = os.path.abspath(os.path.dirname(progpath))
packagename = os.path.basename(packagedir)
bindir = os.path.join(packagedir, 'bin')
if sys.platform == 'win32':
    bindir = os.path.join(bindir, 'win32')
rootdir = os.path.dirname(packagedir)

def prepend_path(name, value):
    sep = os.path.pathsep
    curpath = os.environ.get(name, '')
    newpath = [value] + [ x for x in curpath.split(sep) if x and x != value ]
    return setenv(name, sep.join(newpath))

def setenv(name, value):
    shell = os.environ.get('SHELL', '')
    comspec = os.environ.get('COMSPEC', '')
    if shell.endswith('csh'):
        cmd = 'setenv %s "%s"' % (name, value)
    elif shell.endswith('sh'):
        cmd = '%s="%s"; export %s' % (name, value, name)
    elif comspec.endswith('cmd.exe'):
        cmd = 'set %s=%s' % (name, value)
    else:
        assert False, 'Shell not supported.'
    return cmd

print prepend_path('PATH', bindir)
print prepend_path('PYTHONPATH', rootdir)
