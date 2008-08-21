#!/usr/bin/env python 

"""\
py.lookup SEARCH_STRING [options]

Looks recursively at Python files for a SEARCH_STRING, starting from the
present working directory. Prints the line, with the filename and line-number
prepended."""

import sys, os
import py
from py.__.io.terminalwriter import ansi_print, terminal_width
import re

curdir = py.path.local()
def rec(p):
    return p.check(dotfile=0)

optparse = py.compat.optparse

parser = optparse.OptionParser(usage=__doc__)
parser.add_option("-i", "--ignore-case", action="store_true", dest="ignorecase",
                  help="ignore case distinctions")
parser.add_option("-C", "--context", action="store", type="int", dest="context",
            default=0, help="How many lines of output to show")

def find_indexes(search_line, string):
    indexes = []
    before = 0
    while 1:
        i = search_line.find(string, before)
        if i == -1:
            break
        indexes.append(i)
        before = i + len(string)
    return indexes

def main():
    (options, args) = parser.parse_args()
    string = args[0]
    if options.ignorecase:
        string = string.lower()
    for x in curdir.visit('*.py', rec):
        # match filename directly
        s = x.relto(curdir)
        if options.ignorecase:
            s = s.lower()
        if s.find(string) != -1:
           print >>sys.stdout, "%s: filename matches %r" %(x, string)

        try:
            s = x.read()
        except py.error.ENOENT:
            pass # whatever, probably broken link (ie emacs lock)
        searchs = s
        if options.ignorecase:
            searchs = s.lower()
        if s.find(string) != -1:
            lines = s.splitlines()
            if options.ignorecase:
                searchlines = s.lower().splitlines()
            else:
                searchlines = lines
            for i, (line, searchline) in enumerate(zip(lines, searchlines)): 
                indexes = find_indexes(searchline, string)
                if not indexes:
                    continue
                if not options.context:
                    sys.stdout.write("%s:%d: " %(x.relto(curdir), i+1))
                    last_index = 0
                    for index in indexes:
                        sys.stdout.write(line[last_index: index])
                        ansi_print(line[index: index+len(string)],
                                   file=sys.stdout, esc=31, newline=False)
                        last_index = index + len(string)
                    sys.stdout.write(line[last_index:] + "\n")
                else:
                    context = (options.context)/2
                    for count in range(max(0, i-context), min(len(lines) - 1, i+context+1)):
                        print "%s:%d:  %s" %(x.relto(curdir), count+1, lines[count].rstrip())
                    print "-" * terminal_width
