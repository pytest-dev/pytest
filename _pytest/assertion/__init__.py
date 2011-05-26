"""
support for presented detailed information in failing assertions.
"""
import py
import imp
import marshal
import struct
import sys
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
    group._addoption('--no-assert', action="store_true", default=False,
        dest="noassert",
        help="disable python assert expression reinterpretation."),

def pytest_configure(config):
    global rewrite_asserts
    # The _reprcompare attribute on the py.code module is used by
    # py._code._assertionnew to detect this plugin was loaded and in
    # turn call the hooks defined here as part of the
    # DebugInterpreter.
    m = monkeypatch()
    config._cleanup.append(m.undo)
    warn_about_missing_assertion()
    if not config.getvalue("noassert") and not config.getvalue("nomagic"):
        def callbinrepr(op, left, right):
            hook_result = config.hook.pytest_assertrepr_compare(
                config=config, op=op, left=left, right=right)
            for new_expl in hook_result:
                if new_expl:
                    return '\n~'.join(new_expl)
        m.setattr(py.builtin.builtins, 'AssertionError',
                  reinterpret.AssertionError)
        m.setattr(util, '_reprcompare', callbinrepr)
    else:
        rewrite_asserts = None

def _write_pyc(co, source_path):
    if hasattr(imp, "cache_from_source"):
        # Handle PEP 3147 pycs.
        pyc = py.path(imp.cache_from_source(source_math))
        pyc.dirname.ensure(dir=True)
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

def pytest_pycollect_before_module_import(mod):
    if rewrite_asserts is None:
        return
    # Some deep magic: load the source, rewrite the asserts, and write a
    # fake pyc, so that it'll be loaded when the module is imported.
    source = mod.fspath.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Let this pop up again in the real import.
        return
    rewrite_asserts(tree)
    try:
        co = compile(tree, str(mod.fspath), "exec")
    except SyntaxError:
        # It's possible that this error is from some bug in the assertion
        # rewriting, but I don't know of a fast way to tell.
        return
    mod._pyc = _write_pyc(co, mod.fspath)

def pytest_pycollect_after_module_import(mod):
    if rewrite_asserts is None or not hasattr(mod, "_pyc"):
        return
    # Remove our tweaked pyc to avoid subtle bugs.
    try:
        mod._pyc.remove()
    except py.error.ENOENT:
        pass

def warn_about_missing_assertion():
    try:
        assert False
    except AssertionError:
        pass
    else:
        sys.stderr.write("WARNING: failing tests may report as passing because "
        "assertions are turned off!  (are you using python -O?)\n")

pytest_assertrepr_compare = util.assertrepr_compare
