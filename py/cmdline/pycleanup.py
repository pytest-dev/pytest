#!/usr/bin/env python 

"""\
py.cleanup [PATH]

Delete pyc file recursively, starting from PATH (which defaults to the current
working directory). Don't follow links and don't recurse into directories with
a ".".
"""
import py

def main():
    parser = py.compat.optparse.OptionParser(usage=__doc__)
    (options, args) = parser.parse_args()
    if not args:
        args = ["."]
    for arg in args:
        path = py.path.local(arg)
        print "cleaning path", path
        for x in path.visit('*.pyc', lambda x: x.check(dotfile=0, link=0)):
            x.remove()
