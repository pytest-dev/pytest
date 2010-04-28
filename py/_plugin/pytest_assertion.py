import py
import sys

def pytest_addoption(parser):
    group = parser.getgroup("debugconfig")
    group._addoption('--no-assert', action="store_true", default=False, 
        dest="noassert", 
        help="disable python assert expression reinterpretation."),

def pytest_configure(config):
    if not config.getvalue("noassert") and not config.getvalue("nomagic"):
        warn_about_missing_assertion()
        config._oldassertion = py.builtin.builtins.AssertionError
        py.builtin.builtins.AssertionError = py.code._AssertionError 

def pytest_unconfigure(config):
    if hasattr(config, '_oldassertion'):
        py.builtin.builtins.AssertionError = config._oldassertion
        del config._oldassertion

def warn_about_missing_assertion():
    try:
        assert False
    except AssertionError:
        pass
    else:
        py.std.warnings.warn("Assertions are turned off!"
                             " (are you using python -O?)")
