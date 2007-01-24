#! /usr/bin/env python
"""
a remote python shell

for injection into startserver.py
"""
import sys, os, socket, select

try:
    clientsock
except NameError:
    print "client side starting"
    import sys
    host, port  = sys.argv[1].split(':')
    port = int(port)
    myself = open(os.path.abspath(sys.argv[0]), 'rU').read()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(repr(myself)+'\n')
    print "send boot string"
    inputlist = [ sock, sys.stdin ]
    try:
        while 1:
            r,w,e = select.select(inputlist, [], [])
            if sys.stdin in r:
                line = raw_input()
                sock.sendall(line + '\n')
            if sock in r:
                line = sock.recv(4096)
                sys.stdout.write(line)
                sys.stdout.flush()
    except:
        import traceback
        print traceback.print_exc()

    sys.exit(1)

print "server side starting"
# server side
#
from traceback import print_exc
from threading import Thread

class promptagent(Thread):
    def __init__(self, clientsock):
        Thread.__init__(self)
        self.clientsock = clientsock

    def run(self):
        print "Entering thread prompt loop"
        clientfile = self.clientsock.makefile('w')

        filein = self.clientsock.makefile('r')
        loc = self.clientsock.getsockname()

        while 1:
            try:
                clientfile.write('%s %s >>> ' % loc)
                clientfile.flush()
                line = filein.readline()
                if len(line)==0: raise EOFError,"nothing"
                #print >>sys.stderr,"got line: " + line
                if line.strip():
                    oldout, olderr = sys.stdout, sys.stderr
                    sys.stdout, sys.stderr = clientfile, clientfile
                    try:
                        try:
                            exec compile(line + '\n','<remote pyin>', 'single')
                        except:
                            print_exc()
                    finally:
                        sys.stdout=oldout
                        sys.stderr=olderr
                clientfile.flush()
            except EOFError,e:
                print >>sys.stderr, "connection close, prompt thread returns"
                break
                #print >>sys.stdout, "".join(apply(format_exception,sys.exc_info()))

        self.clientsock.close()

prompter = promptagent(clientsock)
prompter.start()
print "promptagent - thread started"
