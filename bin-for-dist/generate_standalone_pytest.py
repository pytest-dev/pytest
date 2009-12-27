#! /usr/bin/env python

import os
import cPickle
import zlib
import base64
import sys

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    outfile = os.path.join(here, "py.test")
    infile = outfile+"-in"
    
    os.chdir(os.path.dirname(here))

    files = []
    for dirpath, dirnames, filenames in os.walk("py"):
        for f in filenames:
            if not f.endswith(".py"):
                continue
                
            fn = os.path.join(dirpath, f)
            files.append(fn)

    name2src = {}
    for f in files:
        k = f.replace("/", ".")[:-3]
        name2src[k] = open(f, "rb").read()

    data = cPickle.dumps(name2src, 2)
    data = zlib.compress(data, 9)
    data = base64.encodestring(data)

    exe = open(infile, "rb").read()
    exe = exe.replace("@SOURCES@", data)

    open(outfile, "wb").write(exe)
    os.chmod(outfile, 493)  # 0755
    sys.stdout.write("generated %s\n" % outfile)

if __name__=="__main__":
    main()
