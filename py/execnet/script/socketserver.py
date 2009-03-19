#! /usr/bin/env python

"""
    start socket based minimal readline exec server
"""
# this part of the program only executes on the server side
#

progname = 'socket_readline_exec_server-1.2'
debug = 0

import sys, socket, os
try:
    import fcntl
except ImportError:
    fcntl = None

if debug: #  and not os.isatty(sys.stdin.fileno()):
    f = open('/tmp/execnet-socket-pyout.log', 'a', 0)
    old = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = f
    #import py 
    #compile = py.code.compile 

def exec_from_one_connection(serversock):
    print progname, 'Entering Accept loop', serversock.getsockname()
    clientsock,address = serversock.accept()
    print progname, 'got new connection from %s %s' % address
    clientfile = clientsock.makefile('r+',0)
    print "reading line"
    # rstrip so that we can use \r\n for telnet testing
    source = clientfile.readline().rstrip()
    clientfile.close()
    g = {'clientsock' : clientsock, 'address' : address}
    source = eval(source)
    if source:
        co = compile(source+'\n', source, 'exec')
        print progname, 'compiled source, executing'
        try:
            exec co in g
        finally:
            print progname, 'finished executing code'
            # background thread might hold a reference to this (!?)
            #clientsock.close()

def bind_and_listen(hostport):
    if isinstance(hostport, str):
        host, port = hostport.split(':')
        hostport = (host, int(port))
    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # set close-on-exec
    if hasattr(fcntl, 'FD_CLOEXEC'):
        old = fcntl.fcntl(serversock.fileno(), fcntl.F_GETFD)
        fcntl.fcntl(serversock.fileno(), fcntl.F_SETFD, old | fcntl.FD_CLOEXEC)
    # allow the address to be re-used in a reasonable amount of time
    if os.name == 'posix' and sys.platform != 'cygwin':
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    serversock.bind(hostport)
    serversock.listen(5)
    return serversock

def startserver(serversock, loop=False):
    try:
        while 1: 
            try: 
                exec_from_one_connection(serversock)
            except (KeyboardInterrupt, SystemExit): 
                raise 
            except: 
                if debug:
                    import traceback
                    traceback.print_exc()
                else:
                    excinfo = sys.exc_info()
                    print "got exception", excinfo[1]
            if not loop: 
                break 
    finally:
        print "leaving socketserver execloop"
        serversock.shutdown(2)

if __name__ == '__main__':
    import sys
    if len(sys.argv)>1:
        hostport = sys.argv[1]
    else:
        hostport = ':8888'
    serversock = bind_and_listen(hostport)
    startserver(serversock, loop=False)

