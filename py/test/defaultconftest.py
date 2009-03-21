import py

Module = py.test.collect.Module
#DoctestFile = py.test.collect.DoctestFile
Directory = py.test.collect.Directory
Class = py.test.collect.Class
Generator = py.test.collect.Generator
Function = py.test.collect.Function
Instance = py.test.collect.Instance

conf_iocapture = "fd" # overridable from conftest.py 

pytest_plugins = "default terminal xfail tmpdir execnetcleanup monkeypatch".split()

# ===================================================
# settings in conftest only (for now) - for distribution

dist_boxed = False
if hasattr(py.std.os, 'nice'):
    dist_nicelevel = py.std.os.nice(0) # nice py.test works
else:
    dist_nicelevel = 0

