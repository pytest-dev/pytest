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

    old_trace = py.std.pdb.set_trace
    def fin():
        py.std.pdb.set_trace = old_trace
    py.std.pdb.set_trace = pytest.set_trace
    config._cleanup.append(fin)

class pytestPDB:
    """ Pseudo PDB that defers to the real pdb. """
    item = None
    collector = None

    def set_trace(self):
        """ invoke PDB set_trace debugging, dropping any IO capturing. """
        frame = sys._getframe().f_back
        item = self.item or self.collector

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

@pytest.mark.tryfirst
def pytest_make_collect_report(__multicall__, collector):
    try:
        pytestPDB.collector = collector
        return __multicall__.execute()
    finally:
        pytestPDB.collector = None

def pytest_runtest_makereport():
    pytestPDB.item = None

class PdbInvoke:
    def pytest_exception_interact(self, node, call, report):
        return _enter_pdb(node, call.excinfo, report)

    def pytest_internalerror(self, excrepr, excinfo):
        for line in str(excrepr).split("\n"):
            sys.stderr.write("INTERNALERROR> %s\n" %line)
            sys.stderr.flush()
        tb = _postmortem_traceback(excinfo)
        post_mortem(tb)


def _enter_pdb(node, excinfo, rep):
    # XXX we re-use the TerminalReporter's terminalwriter
    # because this seems to avoid some encoding related troubles
    # for not completely clear reasons.
    tw = node.config.pluginmanager.getplugin("terminalreporter")._tw
    tw.line()
    tw.sep(">", "traceback")
    rep.toterminal(tw)
    tw.sep(">", "entering PDB")
    tb = _postmortem_traceback(excinfo)
    post_mortem(tb)
    rep._pdbshown = True
    return rep


def _postmortem_traceback(excinfo):
    # A doctest.UnexpectedException is not useful for post_mortem.
    # Use the underlying exception instead:
    if isinstance(excinfo.value, py.std.doctest.UnexpectedException):
        return excinfo.value.exc_info[2]
    else:
        return excinfo._excinfo[2]


def _find_last_non_hidden_frame(stack):
    i = max(0, len(stack) - 1)
    while i and stack[i][0].f_locals.get("__tracebackhide__", False):
        i -= 1
    return i


def post_mortem(t):
    pdb = py.std.pdb
    class Pdb(pdb.Pdb):
        def get_stack(self, f, t):
            stack, i = pdb.Pdb.get_stack(self, f, t)
            if f is None:
                i = _find_last_non_hidden_frame(stack)
            return stack, i
    p = Pdb()
    p.reset()
    p.interaction(None, t)
