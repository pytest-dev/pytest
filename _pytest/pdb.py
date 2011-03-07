""" interactive debugging with PDB, the Python Debugger. """

import pytest, py
import sys

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('--pdb',
               action="store_true", dest="usepdb", default=False,
               help="start the interactive Python debugger on errors.")

def pytest_namespace():
    return {'set_trace': pytestPDB().set_trace}

def pytest_configure(config):
    if config.getvalue("usepdb"):
        config.pluginmanager.register(PdbInvoke(), 'pdbinvoke')

class pytestPDB:
    """ Pseudo PDB that defers to the real pdb. """
    item = None

    def set_trace(self):
        """ invoke PDB set_trace debugging, dropping any IO capturing. """
        frame = sys._getframe().f_back
        item = getattr(self, 'item', None)
        if item is not None:
            capman = item.config.pluginmanager.getplugin("capturemanager")
            out, err = capman.suspendcapture()
            if hasattr(item, 'outerr'):
                item.outerr = (item.outerr[0] + out, item.outerr[1] + err)
            tw = py.io.TerminalWriter()
            tw.line()
            tw.sep(">", "PDB set_trace (IO-capturing turned off)")
        py.std.pdb.Pdb().set_trace(frame)

def pdbitem(item):
    pytestPDB.item = item
pytest_runtest_setup = pytest_runtest_call = pytest_runtest_teardown = pdbitem

def pytest_runtest_makereport():
    pytestPDB.item = None
    
class PdbInvoke:
    @pytest.mark.tryfirst
    def pytest_runtest_makereport(self, item, call, __multicall__):
        rep = __multicall__.execute()
        if not call.excinfo or \
            call.excinfo.errisinstance(pytest.skip.Exception) or \
            call.excinfo.errisinstance(py.std.bdb.BdbQuit):
            return rep
        if "xfail" in rep.keywords:
            return rep
        # we assume that the above execute() suspended capturing
        # XXX we re-use the TerminalReporter's terminalwriter
        # because this seems to avoid some encoding related troubles
        # for not completely clear reasons.
        tw = item.config.pluginmanager.getplugin("terminalreporter")._tw
        tw.line()
        tw.sep(">", "traceback")
        rep.toterminal(tw)
        tw.sep(">", "entering PDB")
        post_mortem(call.excinfo._excinfo[2])
        rep._pdbshown = True
        return rep

def post_mortem(t):
    pdb = py.std.pdb
    class Pdb(pdb.Pdb):
        def get_stack(self, f, t):
            stack, i = pdb.Pdb.get_stack(self, f, t)
            if f is None:
                i = max(0, len(stack) - 1)
                while i and stack[i][0].f_locals.get("__tracebackhide__", False):
                    i-=1
            return stack, i
    p = Pdb()
    p.reset()
    p.interaction(None, t)
