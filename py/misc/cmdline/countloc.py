#!/usr/bin/env python

# hands on script to compute the non-empty Lines of Code 
# for tests and non-test code 

import py


curdir = py.path.local()

   
def nodot(p):
    return p.check(dotfile=0)

class FileCounter(object):  
    def __init__(self):
        self.file2numlines = {}
        self.numlines = 0
        self.numfiles = 0

    def addrecursive(self, directory, fil="*.py", rec=nodot):
        for x in directory.visit(fil, rec): 
            self.addfile(x)

    def addfile(self, fn, emptylines=False):
        if emptylines:
            s = len(p.readlines())
        else:
            s = 0
            for i in fn.readlines():
                if i.strip():
                    s += 1
        self.file2numlines[fn] = s 
        self.numfiles += 1
        self.numlines += s

    def getnumlines(self, fil): 
        numlines = 0
        for path, value in self.file2numlines.items():
            if fil(path): 
                numlines += value
        return numlines 

    def getnumfiles(self, fil): 
        numfiles = 0
        for path in self.file2numlines:
            if fil(path): 
                numfiles += 1
        return numfiles

def get_loccount(locations=None):
    if locations is None:
        localtions = [py.path.local()]
    counter = FileCounter()
    for loc in locations: 
        counter.addrecursive(loc, '*.py', rec=nodot)

    def istestfile(p):
        return p.check(fnmatch='test_*.py')
    isnottestfile = lambda x: not istestfile(x)

    numfiles = counter.getnumfiles(isnottestfile) 
    numlines = counter.getnumlines(isnottestfile) 
    numtestfiles = counter.getnumfiles(istestfile)
    numtestlines = counter.getnumlines(istestfile)
   
    return counter, numfiles, numlines, numtestfiles, numtestlines

def countloc(paths=None):
    if not paths:
        paths = ['.']
    locations = [py.path.local(x) for x in paths]
    (counter, numfiles, numlines, numtestfiles,
     numtestlines) = get_loccount(locations)

    items = counter.file2numlines.items()
    items.sort(lambda x,y: cmp(x[1], y[1]))
    for x, y in items:
        print "%3d %30s" % (y,x) 
    
    print "%30s %3d" %("number of testfiles", numtestfiles)
    print "%30s %3d" %("number of non-empty testlines", numtestlines)
    print "%30s %3d" %("number of files", numfiles)
    print "%30s %3d" %("number of non-empty lines", numlines)
