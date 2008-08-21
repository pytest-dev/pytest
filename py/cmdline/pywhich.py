#!/usr/bin/env python 

"""\
py.which [name]

print the location of the given python module or package name 
"""

import sys

def main():
    name = sys.argv[1]
    try:
        mod = __import__(name)
    except ImportError:
        print >>sys.stderr, "could not import:", name 
    else:
        try:
            location = mod.__file__ 
        except AttributeError:
            print >>sys.stderr, "module (has no __file__):", mod
        else:
            print location
