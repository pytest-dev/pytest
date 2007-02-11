import py

def deprecated_call(func, *args, **kwargs):
    """ assert that calling func(*args, **kwargs)
        triggers a DeprecationWarning. 
    """ 
    l = []
    oldwarn = py.std.warnings.warn_explicit
    def warn_explicit(*args, **kwargs): 
        l.append(args) 
        oldwarn(*args, **kwargs)
        
    py.magic.patch(py.std.warnings, 'warn_explicit', warn_explicit)
    try:
        _ = func(*args, **kwargs)
    finally:
        py.magic.revert(py.std.warnings, 'warn_explicit')
    assert l
