import py

py.log._apiwarn("1.1", "py.compat.doctest deprecated, use standard library version.", 
stacklevel="apipkg")
doctest = py.std.doctest
