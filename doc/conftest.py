#XXX make work: excludedirs = ['_build']
import py
pytest_plugins = ['pytest_restdoc']
collect_ignore = ['test/attic.txt']

def pytest_runtest_setup(item):
    if item.fspath.ext == ".txt":
        py.test.importorskip("pygments") # for raising an error
