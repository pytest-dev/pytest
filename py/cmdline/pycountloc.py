#!/usr/bin/env python

# hands on script to compute the non-empty Lines of Code 
# for tests and non-test code 

"""\
py.countloc [PATHS]

Count (non-empty) lines of python code and number of python files recursively
starting from a list of paths given on the command line (starting from the
current working directory). Distinguish between test files and normal ones and
report them separately.
"""
import py
from py.compat import optparse
from py.__.misc.cmdline.countloc import countloc 

def main():
    parser = optparse.OptionParser(usage=__doc__)
    (options, args) = parser.parse_args()
    countloc(args)
