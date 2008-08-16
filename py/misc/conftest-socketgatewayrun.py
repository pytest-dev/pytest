"""

Put this file as 'conftest.py' somewhere upwards from py-trunk, 
modify the "socketserveradr" below to point to a windows/linux
host running "py/execnet/script/loop_socketserver.py" 
and invoke e.g. from linux:

    py.test --session=MySession some_path_to_what_you_want_to_test

This should ad-hoc distribute the running of tests to
the remote machine (including rsyncing your WC). 

"""
import py
from py.__.test.looponfail.remote import LooponfailingSession

import os

class MyRSync(py.execnet.RSync):
    def filter(self, path):
        if path.endswith('.pyc') or path.endswith('~'):
            return False
        dir, base = os.path.split(path)
        # we may want to have revision info on the other side,
        # so let's not exclude .svn directories
        #if base == '.svn': 
        #    return False
        return True
    
class MySession(LooponfailingSession):
    socketserveradr = ('10.9.2.62', 8888)
    socketserveradr = ('10.9.4.148', 8888)

    def _initslavegateway(self):
        print "MASTER: initializing remote socket gateway"
        gw = py.execnet.SocketGateway(*self.socketserveradr)
        pkgname = 'py' # xxx flexibilize
        channel = gw.remote_exec("""
            import os
            topdir = os.path.join(os.environ['HOMEPATH'], 'pytestcache')
            pkgdir = os.path.join(topdir, %r)
            channel.send((topdir, pkgdir))
        """ % (pkgname,))
        remotetopdir, remotepkgdir = channel.receive()
        sendpath = py.path.local(py.__file__).dirpath()
        rsync = MyRSync(sendpath)
        rsync.add_target(gw, remotepkgdir, delete=True) 
        rsync.send()
        channel = gw.remote_exec("""
            import os, sys
            path = %r # os.path.abspath
            sys.path.insert(0, path)
            os.chdir(path)
            import py
            channel.send((path, py.__file__))
        """ % remotetopdir)
        topdir, remotepypath = channel.receive()
        assert topdir == remotetopdir, (topdir, remotetopdir)
        assert remotepypath.startswith(topdir), (remotepypath, topdir)
        #print "remote side has rsynced pythonpath ready: %r" %(topdir,)
        return gw, topdir

dist_hosts = ['localhost', 'cobra', 'cobra']
