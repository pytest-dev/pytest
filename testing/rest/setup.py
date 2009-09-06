import py

rootdir = py.path.local(__file__).dirpath()
mydatadir = py.path.local(__file__).dirpath('data')

def getdata():
    rel = mydatadir.relto(rootdir)
    tmpdir = py.test.ensuretemp(rel.replace(rootdir.sep, '_'))
    mydatadir.copy(tmpdir)
    return tmpdir

