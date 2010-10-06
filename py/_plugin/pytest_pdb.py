"""
interactive debugging with the Python Debugger.
"""
import py
import sys

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('--pdb',
               action="store_true", dest="usepdb", default=False,
               help="start the interactive Python debugger on errors.")

def pytest_configure(config):
    if config.getvalue("usepdb"):
        config.pluginmanager.register(PdbInvoke(), 'pdb')

class PdbInvoke:
    def pytest_sessionfinish(self, session):
        # don't display failures again at the end
        session.config.option.tbstyle = "no"
    def pytest_runtest_makereport(self, item, call, __multicall__):
        if not call.excinfo or \
            call.excinfo.errisinstance(py.test.skip.Exception) or \
            call.excinfo.errisinstance(py.std.bdb.BdbQuit):
            return
        rep = __multicall__.execute()
        if "xfail" in rep.keywords:
            return rep
        # we assume that the above execute() suspended capturing
        tw = py.io.TerminalWriter()
        tw.line()
        tw.sep(">", "traceback")
        rep.toterminal(tw)
        tw.sep(">", "entering PDB")
        post_mortem(call.excinfo._excinfo[2])
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
