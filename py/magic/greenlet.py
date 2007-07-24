import sys
if '_stackless' in sys.builtin_module_names:
    # when running on top of a pypy with stackless support
    from _stackless import greenlet
elif hasattr(sys, 'pypy_objspaceclass'):
    raise ImportError("Detected pypy without stackless support")
else:
    # regular CPython
    import py
    gdir = py.path.local(py.__file__).dirpath() 
    path = gdir.join('c-extension', 'greenlet', 'greenlet.c')
    greenlet = path._getpymodule().greenlet 
