#! /usr/bin/env python
"""
generate standalone test script to be distributed along with an application. 
"""

import os
import sys
def pytest_addoption(parser):
    group = parser.getgroup("debugconfig")
    group.addoption("--genscript", action="store", default=None, 
        dest="genscript", metavar="path", 
        help="create standalone py.test script at given target path.")

def pytest_configure(config):
    genscript = config.getvalue("genscript")
    if genscript:
        import py
        mydir = py.path.local(__file__).dirpath()
        infile = mydir.join("standalonetemplate.py")
        pybasedir = py.path.local(py.__file__).dirpath().dirpath()
        genscript = py.path.local(genscript)
        main(pybasedir, outfile=genscript, infile=infile)
        raise SystemExit(0)

def main(pybasedir, outfile, infile):
    import base64
    import zlib
    try:
        import pickle
    except Importerror:
        import cPickle as pickle

    outfile = str(outfile)
    infile = str(infile)
    assert os.path.isabs(outfile)
    os.chdir(str(pybasedir))
    files = []
    for dirpath, dirnames, filenames in os.walk("py"):
        for f in filenames:
            if not f.endswith(".py"):
                continue
                
            fn = os.path.join(dirpath, f)
            files.append(fn)

    name2src = {}
    for f in files:
        k = f.replace(os.sep, ".")[:-3]
        name2src[k] = open(f, "r").read()

    data = pickle.dumps(name2src, 2)
    data = zlib.compress(data, 9)
    data = base64.encodestring(data)
    data = data.decode("ascii")

    exe = open(infile, "r").read()
    exe = exe.replace("@SOURCES@", data)

    open(outfile, "w").write(exe)
    os.chmod(outfile, 493)  # 0755
    sys.stdout.write("generated standalone py.test at %r, have fun!\n" % outfile)

if __name__=="__main__":
    dn = os.path.dirname
    here = os.path.abspath(dn(__file__)) # py/plugin/
    pybasedir = dn(dn(here))
    outfile = os.path.join(os.getcwd(), "py.test-standalone")
    infile = os.path.join(here, 'standalonetemplate.py')
    main(pybasedir, outfile, infile)
