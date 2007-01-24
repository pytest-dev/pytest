#!/usr/bin/python

import py

for x in py.path.local(): 
    if x.ext == '.txt':
        cmd = ("python /home/hpk/projects/docutils/tools/rst2s5.py "
               "%s %s" %(x, x.new(ext='.html')))
        print "execing", cmd
        py.std.os.system(cmd) 

