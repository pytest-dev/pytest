from __future__ import generators

import py
from py.__.misc import rest

def setup_module(mod):
    if not py.path.local.sysfind("gs") or \
           not py.path.local.sysfind("dot") or \
           not py.path.local.sysfind("latex"):
        py.test.skip("ghostscript, graphviz and latex needed")
    try:
        import docutils
    except ImportError:
        py.test.skip("docutils not present")

data = py.magic.autopath().dirpath().join("data")

def test_process_simple():
    # fallback test: only checks that no exception is raised
    def rec(p):
        return p.check(dotfile=0)
    for x in data.visit("*.txt", rec=rec):
        yield rest.process, x

