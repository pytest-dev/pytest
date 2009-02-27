import py

Module = py.test.collect.Module
#DoctestFile = py.test.collect.DoctestFile
Directory = py.test.collect.Directory
Class = py.test.collect.Class
Generator = py.test.collect.Generator
Function = py.test.collect.Function
Instance = py.test.collect.Instance

conf_iocapture = "fd" # overridable from conftest.py 

# XXX resultlog should go, pypy's nightrun depends on it
pytest_plugins = "default terminal xfail tmpdir resultlog monkeypatch".split()

# ===================================================
# Distributed testing specific options 

#dist_hosts: needs to be provided by user
#dist_rsync_roots: might be provided by user, if not present or None,
#                  whole pkgdir will be rsynced

dist_taskspernode = 15
dist_boxed = False
if hasattr(py.std.os, 'nice'):
    dist_nicelevel = py.std.os.nice(0) # nice py.test works
else:
    dist_nicelevel = 0
dist_rsync_ignore = []

