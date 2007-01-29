
""" RSync filter test
"""

import py
from py.__.test.rsession.hostmanage import HostRSync

def test_rsync():
    tmpdir = py.test.ensuretemp("rsync_rsession")
    tmpdir.ensure("a", dir=True)
    tmpdir.ensure("b", dir=True)
    tmpdir.ensure("conftest.py").write(py.code.Source("""
    dist_rsyncroots = ['a']
    """))
    tmpdir.join("a").ensure("x")
    adir = tmpdir.join("a").ensure("xy", dir=True)
    adir.ensure("conftest.py").write(py.code.Source("""
    dist_rsyncroots = ['b', 'conftest.py']
    """))
    adir.ensure("a", dir=True)
    adir.ensure("b", dir=True)
    config = py.test.config._reparse([str(tmpdir)])
    h = HostRSync(config)
    h.sourcedir = config.topdir
    assert h.filter(str(tmpdir.join("a")))
    assert not h.filter(str(tmpdir.join("b")))
    assert h.filter(str(tmpdir.join("a").join("x")))
    assert h.filter(str(adir.join("conftest.py")))
    assert not h.filter(str(adir.join("a")))
    assert h.filter(str(adir.join("b")))
