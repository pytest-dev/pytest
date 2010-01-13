
import py
py.log._apiwarn("1.1", "py.compat.subprocess deprecated, use standard library version.", 
stacklevel="apipkg")
subprocess = py.std.subprocess
