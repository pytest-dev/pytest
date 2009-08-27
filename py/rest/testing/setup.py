import py

pydir = py.path.local(py.__file__).dirpath()
mydatadir = py.path.local(__file__).dirpath('data')

def getdata():
    rel = mydatadir.relto(pydir)
    tmpdir = py.test.ensuretemp(rel.replace(pydir.sep, '_'))
    mydatadir.copy(tmpdir)
    return tmpdir

