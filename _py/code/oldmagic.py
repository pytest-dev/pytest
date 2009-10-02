""" deprecated module for turning on/off some features. """ 

import py 

from py.builtin import builtins as cpy_builtin

def invoke(assertion=False, compile=False):
    """ (deprecated) invoke magic, currently you can specify:

        assertion  patches the builtin AssertionError to try to give
                   more meaningful AssertionErrors, which by means
                   of deploying a mini-interpreter constructs
                   a useful error message.
    """
    py.log._apiwarn("1.1", 
        "py.magic.invoke() is deprecated, use py.code.patch_builtins()",
        stacklevel=2, 
    )
    py.code.patch_builtins(assertion=assertion, compile=compile)

def revoke(assertion=False, compile=False):
    """ (deprecated) revoke previously invoked magic (see invoke())."""
    py.log._apiwarn("1.1", 
        "py.magic.revoke() is deprecated, use py.code.unpatch_builtins()",
        stacklevel=2, 
    )
    py.code.unpatch_builtins(assertion=assertion, compile=compile)

patched = {}

def patch(namespace, name, value):
    """ (deprecated) rebind the 'name' on the 'namespace'  to the 'value',
        possibly and remember the original value. Multiple
        invocations to the same namespace/name pair will
        remember a list of old values.
    """
    py.log._apiwarn("1.1", 
        "py.magic.patch() is deprecated, in tests use monkeypatch funcarg.", 
        stacklevel=2, 
    )
    nref = (namespace, name)
    orig = getattr(namespace, name)
    patched.setdefault(nref, []).append(orig)
    setattr(namespace, name, value)
    return orig

def revert(namespace, name):
    """ (deprecated) revert to the orginal value the last patch modified.
        Raise ValueError if no such original value exists.
    """
    py.log._apiwarn("1.1", 
        "py.magic.revert() is deprecated, in tests use monkeypatch funcarg.",
        stacklevel=2, 
    )
    nref = (namespace, name)
    if nref not in patched or not patched[nref]:
        raise ValueError("No original value stored for %s.%s" % nref)
    current = getattr(namespace, name)
    orig = patched[nref].pop()
    setattr(namespace, name, orig)
    return current

