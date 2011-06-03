"""
support for presenting detailed information in failing assertions.
"""
import py
import imp
import marshal
import struct
import sys
import pytest
from _pytest.monkeypatch import monkeypatch
from _pytest.assertion import reinterpret, util

try:
    from _pytest.assertion.rewrite import rewrite_asserts
except ImportError:
    rewrite_asserts = None
else:
    import ast

def pytest_addoption(parser):
    group = parser.getgroup("debugconfig")
    group.addoption('--assertmode', action="store", dest="assertmode",
                    choices=("on", "old", "off", "default"), default="default",
                    metavar="on|old|off",
                    help="""control assertion debugging tools.
'off' performs no assertion debugging.
'old' reinterprets the expressions in asserts to glean information.
'on' (the default) rewrites the assert statements in test modules to provide
sub-expression results.""")
    group.addoption('--no-assert', action="store_true", default=False,
        dest="noassert", help="DEPRECATED equivalent to --assertmode=off")
    group.addoption('--nomagic', action="store_true", default=False,
        dest="nomagic", help="DEPRECATED equivalent to --assertmode=off")

class AssertionState:
    """State for the assertion plugin."""

    def __init__(self, config, mode):
        self.mode = mode
        self.trace = config.trace.root.get("assertion")

def pytest_configure(config):
    warn_about_missing_assertion()
    mode = config.getvalue("assertmode")
    if config.getvalue("noassert") or config.getvalue("nomagic"):
        if mode not in ("off", "default"):
            raise pytest.UsageError("assertion options conflict")
        mode = "off"
    elif mode == "default":
        mode = "on"
    if mode != "off":
        def callbinrepr(op, left, right):
            hook_result = config.hook.pytest_assertrepr_compare(
                config=config, op=op, left=left, right=right)
            for new_expl in hook_result:
                if new_expl:
                    return '\n~'.join(new_expl)
        m = monkeypatch()
        config._cleanup.append(m.undo)
        m.setattr(py.builtin.builtins, 'AssertionError',
                  reinterpret.AssertionError)
        m.setattr(util, '_reprcompare', callbinrepr)
    if mode == "on" and rewrite_asserts is None:
        mode = "old"
    config._assertstate = AssertionState(config, mode)
    config._assertstate.trace("configured with mode set to %r" % (mode,))

def _write_pyc(co, source_path):
    if hasattr(imp, "cache_from_source"):
        # Handle PEP 3147 pycs.
        pyc = py.path.local(imp.cache_from_source(str(source_path)))
        pyc.ensure()
    else:
        pyc = source_path + "c"
    mtime = int(source_path.mtime())
    fp = pyc.open("wb")
    try:
        fp.write(imp.get_magic())
        fp.write(struct.pack("<l", mtime))
        marshal.dump(co, fp)
    finally:
        fp.close()
    return pyc

def before_module_import(mod):
    if mod.config._assertstate.mode != "on":
        return
    # Some deep magic: load the source, rewrite the asserts, and write a
    # fake pyc, so that it'll be loaded when the module is imported.
    source = mod.fspath.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Let this pop up again in the real import.
        mod.config._assertstate.trace("failed to parse: %r" % (mod.fspath,))
        return
    rewrite_asserts(tree)
    try:
        co = compile(tree, str(mod.fspath), "exec")
    except SyntaxError:
        # It's possible that this error is from some bug in the assertion
        # rewriting, but I don't know of a fast way to tell.
        mod.config._assertstate.trace("failed to compile: %r" % (mod.fspath,))
        return
    mod._pyc = _write_pyc(co, mod.fspath)
    mod.config._assertstate.trace("wrote pyc: %r" % (mod._pyc,))

def after_module_import(mod):
    if not hasattr(mod, "_pyc"):
        return
    state = mod.config._assertstate
    try:
        mod._pyc.remove()
    except py.error.ENOENT:
        state.trace("couldn't find pyc: %r" % (mod._pyc,))
    else:
        state.trace("removed pyc: %r" % (mod._pyc,))

def warn_about_missing_assertion():
    try:
        assert False
    except AssertionError:
        pass
    else:
        sys.stderr.write("WARNING: failing tests may report as passing because "
        "assertions are turned off!  (are you using python -O?)\n")

pytest_assertrepr_compare = util.assertrepr_compare
