"""
support for presenting detailed information in failing assertions.
"""
import py
import sys
from _pytest.monkeypatch import monkeypatch
from _pytest.assertion import util

def pytest_addoption(parser):
    group = parser.getgroup("debugconfig")
    group.addoption('--assert', action="store", dest="assertmode",
                    choices=("rewrite", "reinterp", "plain",),
                    default="rewrite", metavar="MODE",
                    help="""control assertion debugging tools.
'plain' performs no assertion debugging.
'reinterp' reinterprets assert statements after they failed to provide assertion expression information.
'rewrite' (the default) rewrites assert statements in test modules on import
to provide assert expression information. """)
    group.addoption('--no-assert', action="store_true", default=False,
        dest="noassert", help="DEPRECATED equivalent to --assert=plain")
    group.addoption('--nomagic', '--no-magic', action="store_true",
        default=False, help="DEPRECATED equivalent to --assert=plain")

class AssertionState:
    """State for the assertion plugin."""

    def __init__(self, config, mode):
        self.mode = mode
        self.trace = config.trace.root.get("assertion")

def pytest_configure(config):
    mode = config.getvalue("assertmode")
    if config.getvalue("noassert") or config.getvalue("nomagic"):
        mode = "plain"
    if mode == "rewrite":
        try:
            import ast  # noqa
        except ImportError:
            mode = "reinterp"
        else:
            # Both Jython and CPython 2.6.0 have AST bugs that make the
            # assertion rewriting hook malfunction.
            if (sys.platform.startswith('java') or
                sys.version_info[:3] == (2, 6, 0)):
                mode = "reinterp"
    if mode != "plain":
        _load_modules(mode)
        m = monkeypatch()
        config._cleanup.append(m.undo)
        m.setattr(py.builtin.builtins, 'AssertionError',
                  reinterpret.AssertionError)  # noqa
    hook = None
    if mode == "rewrite":
        hook = rewrite.AssertionRewritingHook()  # noqa
        sys.meta_path.insert(0, hook)
    warn_about_missing_assertion(mode)
    config._assertstate = AssertionState(config, mode)
    config._assertstate.hook = hook
    config._assertstate.trace("configured with mode set to %r" % (mode,))

def pytest_unconfigure(config):
    hook = config._assertstate.hook
    if hook is not None:
        sys.meta_path.remove(hook)

def pytest_collection(session):
    # this hook is only called when test modules are collected
    # so for example not in the master process of pytest-xdist
    # (which does not collect test modules)
    hook = session.config._assertstate.hook
    if hook is not None:
        hook.set_session(session)

def pytest_runtest_setup(item):
    def callbinrepr(op, left, right):
        hook_result = item.ihook.pytest_assertrepr_compare(
            config=item.config, op=op, left=left, right=right)

        for new_expl in hook_result:
            if new_expl:
                # Don't include pageloads of data unless we are very
                # verbose (-vv)
                if (sum(len(p) for p in new_expl[1:]) > 80*8
                        and item.config.option.verbose < 2):
                    new_expl[1:] = [py.builtin._totext(
                        'Detailed information truncated, use "-vv" to show')]
                res = py.builtin._totext('\n~').join(new_expl)
                if item.config.getvalue("assertmode") == "rewrite":
                    # The result will be fed back a python % formatting
                    # operation, which will fail if there are extraneous
                    # '%'s in the string. Escape them here.
                    res = res.replace("%", "%%")
                return res
    util._reprcompare = callbinrepr

def pytest_runtest_teardown(item):
    util._reprcompare = None

def pytest_sessionfinish(session):
    hook = session.config._assertstate.hook
    if hook is not None:
        hook.session = None

def _load_modules(mode):
    """Lazily import assertion related code."""
    global rewrite, reinterpret
    from _pytest.assertion import reinterpret  # noqa
    if mode == "rewrite":
        from _pytest.assertion import rewrite  # noqa

def warn_about_missing_assertion(mode):
    try:
        assert False
    except AssertionError:
        pass
    else:
        if mode == "rewrite":
            specifically = ("assertions which are not in test modules "
                            "will be ignored")
        else:
            specifically = "failing tests may report as passing"

        sys.stderr.write("WARNING: " + specifically +
                        " because assert statements are not executed "
                        "by the underlying Python interpreter "
                        "(are you using python -O?)\n")

pytest_assertrepr_compare = util.assertrepr_compare
