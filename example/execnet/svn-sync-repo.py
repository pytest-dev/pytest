#!/usr/bin/env python 

import py
import sys, os

def usage():
    arg0 = sys.argv[0]
    print """%s [user@]remote-host:/repo/location localrepo [identity keyfile]""" % (arg0,)


def main(args):
    remote = args[0]
    localrepo = py.path.local(args[1])
    if not localrepo.check(dir=1):
        raise SystemExit("localrepo %s does not exist" %(localrepo,))
    if len(args) == 3:
        keyfile = py.path.local(args[2])
    else:
        keyfile = None
    remote_host, path = remote.split(':', 1)
    print "ssh-connecting to", remote_host 
    gw = getgateway(remote_host, keyfile)

    local_rev = get_svn_youngest(localrepo)

    # local protocol 
    # 1. client sends rev/repo -> server 
    # 2. server checks for newer revisions and sends dumps 
    # 3. client receives dumps, updates local repo 
    # 4. client goes back to step 1
    c = gw.remote_exec("""
        import py
        import os
        remote_rev, repopath = channel.receive()
        while 1: 
            rev = py.process.cmdexec('svnlook youngest "%s"' % repopath) 
            rev = int(rev)
            if rev > remote_rev:
                revrange = (remote_rev+1, rev)
                dumpchannel = channel.gateway.newchannel()
                channel.send(revrange)
                channel.send(dumpchannel)

                f = os.popen(
                        "svnadmin dump -q --incremental -r %s:%s %s" 
                         % (revrange[0], revrange[1], repopath), 'r')
                try:
                    while 1:
                        s = f.read(8192)
                        if not s:
                            raise EOFError
                        dumpchannel.send(s)
                except EOFError:
                    dumpchannel.close()
                remote_rev = rev 
            else:
                # using svn-hook instead would be nice here
                py.std.time.sleep(30)
    """)

    c.send((local_rev, path))
    print "checking revisions from %d in %s" %(local_rev, remote)
    while 1: 
        revstart, revend = c.receive()
        dumpchannel = c.receive() 

        print "receiving revisions", revstart, "-", revend, "replaying..."
        svn_load(localrepo, dumpchannel)
        print "current revision", revend 

def svn_load(repo, dumpchannel):
    f = os.popen("svnadmin load -q %s" %(repo, ), "w")
    for x in dumpchannel:
        sys.stdout.write(".")
        sys.stdout.flush()
        f.write(x)
    print >>sys.stdout
    f.close() 

def get_svn_youngest(repo):
    rev = py.process.cmdexec('svnlook youngest "%s"' % repo) 
    return int(rev)

def getgateway(host, keyfile=None):
    return execnet.SshGateway(host, identity=keyfile)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        usage()
        raise SystemExit(1)

    main(sys.argv[1:])

