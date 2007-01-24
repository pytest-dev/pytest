import py 
import __builtin__ as cpy_builtin

def invoke(assertion=False, compile=False):
    """ invoke magic, currently you can specify:

        assertion  patches the builtin AssertionError to try to give
                   more meaningful AssertionErrors, which by means
                   of deploying a mini-interpreter constructs
                   a useful error message.
    """
    if assertion:
        from py.__.magic import assertion
        assertion.invoke()
    if compile: 
        py.magic.patch(cpy_builtin, 'compile', py.code.compile )

def revoke(assertion=False, compile=False):
    """ revoke previously invoked magic (see invoke())."""
    if assertion:
        from py.__.magic import assertion
        assertion.revoke()
    if compile: 
        py.magic.revert(cpy_builtin, 'compile') 
