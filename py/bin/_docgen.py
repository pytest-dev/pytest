#!/usr/bin/env python

""" quick tool to get documentation + apigen docs generated

    given a certain targetpath, apigen docs will be placed in 'apigen',

    user can choose to only build either docs or apigen docs: in this case,
    the navigation bar will be adjusted
"""

from _findpy import py
import py
pypath = py.__package__.getpath()

def run_tests(path, envvars='', args=''):
    pytestpath = pypath.join('bin/py.test')
    cmd = ('PYTHONPATH="%s" %s python "%s" %s "%s"' %
            (pypath.dirpath(), envvars, pytestpath, args, path))
    print cmd
    py.process.cmdexec(cmd)

def build_apigen_docs(targetpath, testargs=''):
    run_tests(pypath,
              'APIGEN_TARGET="%s/apigen" APIGEN_DOCRELPATH="../"' % (
               targetpath,),
              '%s --apigen="%s/apigen/apigen.py"' % (testargs, pypath))

def build_docs(targetpath, testargs):
    docpath = pypath.join('doc')
    run_tests(docpath, '',
              testargs + ' --forcegen --apigen="%s/apigen/apigen.py"' % (pypath,))
    docpath.copy(targetpath)

def build_nav(targetpath, docs=True, api=True):
    pass

def build(targetpath, docs=True, api=True, testargs=''):
    targetpath.ensure(dir=True)
    if docs:
        print 'building docs'
        build_docs(targetpath, testargs)
    if api:
        print 'building api'
        build_apigen_docs(targetpath, testargs)
        
if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        print 'usage: %s <targetdir> [options]'
        print
        print '  targetdir: a path to a directory (created if it doesn\'t'
        print '             exist) where the docs are put'
        print '  options: options passed to py.test when running the tests'
        sys.exit(1)
    targetpath = py.path.local(sys.argv[1])
    args = ' '.join(sys.argv[2:])
    build(targetpath, True, True, args)

