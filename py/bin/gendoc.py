#!/usr/bin/env python

import sys
import os
from _findpy import py
try:
    import apigen
except ImportError:
    print 'Can not find apigen - make sure PYTHONPATH is set correctly!'
    py.std.sys.exit()
else:
    args = list(sys.argv[1:])
    argkeys = [a.split('=')[0] for a in args]
    if '--apigen' not in argkeys:
        args.append('--apigen')
    if '--apigenscript' not in argkeys:
        fpath = os.path.join(
            os.path.dirname(apigen.__file__), 'tool', 'py_build', 'build.py')
        args.append('--apigenscript=%s' % (fpath,))
    if '--apigenpath' not in argkeys:
        args.append('--apigenpath=/tmp/pylib-api')
    py.test.cmdline.main(args)
