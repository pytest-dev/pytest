"""
support for presenting detailed information in failing assertions.
"""
import py
import sys
import pytest
from _pytest.monkeypatch import monkeypatch
from _pytest.assertion import util

REWRITING_AVAILABLE = "_ast" in sys.builtin_module_names

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
        self.pycs = []

def pytest_configure(config):
    mode = config.getvalue("assertmode")
    if config.getvalue("noassert") or config.getvalue("nomagic"):
        if mode not in ("off", "default"):
            raise pytest.UsageError("assertion options conflict")
        mode = "off"
    elif mode == "default":
        mode = "on"
    if mode == "on" and not REWRITING_AVAILABLE:
        mode = "old"
    if mode != "off":
        _load_modules(mode)
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
    hook = None
    if mode == "on":
        hook = rewrite.AssertionRewritingHook()
        sys.meta_path.append(hook)
    warn_about_missing_assertion(mode)
    config._assertstate = AssertionState(config, mode)
    config._assertstate.hook = hook
    config._assertstate.trace("configured with mode set to %r" % (mode,))

def pytest_unconfigure(config):
    if config._assertstate.mode == "on":
        rewrite._drain_pycs(config._assertstate)
    hook = config._assertstate.hook
    if hook is not None:
        sys.meta_path.remove(hook)

def pytest_sessionstart(session):
    hook = session.config._assertstate.hook
    if hook is not None:
        hook.set_session(session)

def pytest_sessionfinish(session):
    if session.config._assertstate.mode == "on":
        rewrite._drain_pycs(session.config._assertstate)
    hook = session.config._assertstate.hook
    if hook is not None:
        hook.session = None

def _load_modules(mode):
    """Lazily import assertion related code."""
    global rewrite, reinterpret
    from _pytest.assertion import reinterpret
    if mode == "on":
        from _pytest.assertion import rewrite

def warn_about_missing_assertion(mode):
    try:
        assert False
    except AssertionError:
        pass
    else:
        if mode == "on":
            specifically = ("assertions which are not in test modules "
                            "will be ignored")
        else:
            specifically = "failing tests may report as passing"

        sys.stderr.write("WARNING: " + specifically +
                        " because assertions are turned off "
                        "(are you using python -O?)\n")

pytest_assertrepr_compare = util.assertrepr_compare
