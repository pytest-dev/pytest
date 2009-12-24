#XXX make work: excludedirs = ['_build']
import py
#py.test.importorskip("pygments")
pytest_plugins = ['pytest_restdoc']
collect_ignore = ['test/attic.txt']
