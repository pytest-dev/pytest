import py

py.log._apiwarn("1.1", "py.compat.textwrap deprecated, use standard library version.", 
    stacklevel="apipkg")
textwrap = py.std.textwrap
