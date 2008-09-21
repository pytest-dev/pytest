from __future__ import generators

import py
from py.__.misc import rest
from py.__.rest.testing.setup import getdata


def setup_module(mod):
    py.test.importorskip("docutils")
    if not py.path.local.sysfind("gs") or \
           not py.path.local.sysfind("dot") or \
           not py.path.local.sysfind("latex"):
        py.test.skip("ghostscript, graphviz and latex needed")
    mod.datadir = getdata()

def test_process_simple():
    # fallback test: only checks that no exception is raised
    def rec(p):
        return p.check(dotfile=0)
    for x in datadir.visit("*.txt", rec=rec):
        yield rest.process, x

