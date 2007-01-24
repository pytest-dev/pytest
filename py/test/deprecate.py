import py

def deprecated_call(func, *args, **kwargs): 
    """ assert that calling func(*args, **kwargs)
        triggers a DeprecationWarning. 
    """ 
    oldfilters = py.std.warnings.filters[:]
    onceregistry = py.std.warnings.onceregistry.copy()
    try: 
        py.std.warnings.onceregistry.clear()
        py.std.warnings.filterwarnings("error", category=DeprecationWarning)
        try:
            _ = func(*args, **kwargs) 
        except DeprecationWarning: 
            pass
        else:
            print __warningregistry__
            raise AssertionError("%s not deprecated" % (func,))
    finally: 
        py.std.warnings.filters[:] = oldfilters 
        py.std.warnings.onceregistry.clear()
        py.std.warnings.onceregistry.update(onceregistry) 

def deprecated_call(func, *args, **kwargs):
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
