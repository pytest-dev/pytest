#!/usr/bin/env python
"""
invoke 

    py.rest filename1.txt directory 

to generate html files from ReST.

It is also possible to generate pdf files using the --topdf option.

http://docutils.sourceforge.net/docs/user/rst/quickref.html

"""

import os, sys
import py

if hasattr(sys.stdout, 'fileno') and os.isatty(sys.stdout.fileno()):
    def log(msg):
        print msg
else:
    def log(msg):
        pass

optparse = py.compat.optparse

parser = optparse.OptionParser(usage=__doc__)
parser.add_option("--topdf", action="store_true", dest="topdf", default=False,
                  help="generate pdf files")
parser.add_option("--stylesheet", dest="stylesheet", default=None,
                  help="use specified latex style sheet")
parser.add_option("--debug", action="store_true", dest="debug",
                  default=False,
                  help="print debug output and don't delete files")


def main():
    try:
        from py.__.misc import rest
        from py.__.rest import directive
        from py.__.rest.latex import process_rest_file, process_configfile
    except ImportError, e:
        print str(e)
        sys.exit(1)

    (options, args) = parser.parse_args()

    if len(args) == 0:
        filenames = [py.path.svnwc()]
    else:
        filenames = [py.path.svnwc(x) for x in args]
    
    if options.topdf:
        directive.set_backend_and_register_directives("latex")
        
    for p in filenames:
        if not p.check():
            log("path %s not found, ignoring" % p)
            continue
        def fil(p):
            return p.check(fnmatch='*.txt', versioned=True)
        def rec(p):
            return p.check(dotfile=0)
        if p.check(dir=1):
            for x in p.visit(fil, rec):
                rest.process(x)
        elif p.check(file=1):
            if p.ext == ".rst2pdfconfig":
                directive.set_backend_and_register_directives("latex")
                process_configfile(p, options.debug)
            else:
                if options.topdf:
                    cfg = p.new(ext=".rst2pdfconfig")
                    if cfg.check():
                        print "using config file %s" % (cfg, )
                        process_configfile(cfg, options.debug)
                    else:
                        process_rest_file(p.localpath,
                                          options.stylesheet,
                                      options.debug)
                else:
                    rest.process(p)

