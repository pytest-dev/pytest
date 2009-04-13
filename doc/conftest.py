#XXX make work: excludedirs = ['_build']
import py
py.test.importorskip("pygments")
pytest_plugins = ['pytest_restdoc']
rsyncdirs = ['.']
