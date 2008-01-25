
""" some example for running box stuff inside
"""

import sys
import py, os

def boxf1():
    print "some out"
    print >>sys.stderr, "some err"
    return 1

def boxf2():
    os.write(1, "someout")
    os.write(2, "someerr")
    return 2

def boxseg():
    os.kill(os.getpid(), 11)

def boxhuge():
    os.write(1, " " * 10000)
    os.write(2, " " * 10000)
    os.write(1, " " * 10000)
    
    os.write(1, " " * 10000)
    os.write(2, " " * 10000)
    os.write(2, " " * 10000)
    os.write(1, " " * 10000)
    return 3
