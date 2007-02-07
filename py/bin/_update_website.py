#!/usr/bin/env python

""" run py.test with the --apigen option and rsync the results to a host

    rsyncs the whole package (with all the ReST docs converted to HTML) as well
    as the apigen docs to a given remote host and path
"""

import py
import sys

def rsync(pkgpath, apidocspath, gateway, remotepath):
    """ copy the code and docs to the remote host """
    # copy to a temp dir first, even though both paths (normally) share the
    # same parent dir, that may contain other stuff that we don't want to
    # copy...
    tempdir = py.test.ensuretemp('update_website_rsync_temp')
    pkgpath.copy(tempdir.ensure(pkgpath.basename, dir=True))
    apidocspath.copy(tempdir.ensure(apidocspath.basename, dir=True))

    rs = py.execnet.RSync(delete=True)
    rs.add_target(gateway, remotepath)
    rs.send(tempdir)

def run_tests(pkgpath, args=''):
    """ run the unit tests and build the docs """
    pypath = py.__package__.getpath()
    pytestpath = pypath.join('bin/py.test')
    # XXX this would need a Windows specific version if we want to allow
    # running this script on that platform, but currently --apigen doesn't
    # work there anyway...
    apigenpath = pkgpath.join('apigen/apigen.py') # XXX be more general here?
    if not apigenpath.check(file=True):
        apigenpath = pypath.join('apigen/apigen.py')
    cmd = 'PYTHONPATH="%s:%s" python "%s" --apigen="%s" "%s" %s' % (
                                                             pypath.dirpath(),
                                                             pkgpath.dirpath(),
                                                             pytestpath,
                                                             apigenpath,
                                                             pkgpath,
                                                             args)
    status = py.std.os.system(cmd)
    return status

def main(pkgpath, apidocspath, rhost, rpath, args=''):
    print 'running tests'
    errors = run_tests(pkgpath, args)
    if errors:
        print >>sys.stderr, \
              'Errors while running the unit tests: %s' % (errors,)
        sys.exit(1)
    
    print 'rsyncing'
    gateway = py.execnet.SshGateway(rhost)
    errors = rsync(pkgpath, apidocspath, gateway, rpath)
    if errors:
        print >>sys.stderr, 'Errors while rsyncing: %s'
        sys.exit(1)

if __name__ == '__main__':
    args = ' '.join(sys.argv[1:])
    pkgpath = py.__package__.getpath()
    apidocspath = pkgpath.dirpath().join('apigen')
    main(pkgpath, apidocspath, 'codespeak.net',
         '/home/guido/rsynctests', args)

