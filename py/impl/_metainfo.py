
import py

pydir = py.path.local(py.__file__).dirpath()
impldir = pydir.join("impl")

# list of all directories beloging to py
assert impldir.relto(pydir)
pydirs = [pydir]
