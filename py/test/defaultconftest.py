import py

Module = py.test.collect.Module
Directory = py.test.collect.Directory
File = py.test.collect.File

# python collectors 
Class = py.test.collect.Class
Generator = py.test.collect.Generator
Function = py.test.collect.Function
Instance = py.test.collect.Instance

pytest_plugins = "default iocapture runner terminal keyword xfail tmpdir execnetcleanup monkeypatch recwarn pdb unittest".split()

