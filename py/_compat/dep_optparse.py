import py
py.log._apiwarn("1.1", "py.compat.optparse deprecated, use standard library version.", stacklevel="apipkg")

optparse = py.std.optparse 
