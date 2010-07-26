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
        sys.stderr.write("could not import: " +  name + "\n")
    else:
        try:
            location = mod.__file__
        except AttributeError:
            sys.stderr.write("module (has no __file__): " + str(mod))
        else:
            print(location)
