
import py
from py.__.test.outcome import Skipped, Failed, Passed

def setup_module(mod): 
    mod.tmpdir = py.test.ensuretemp('docdoctest')

def test_doctest_extra_exec(): 
    # XXX get rid of the next line: 
    py.magic.autopath().dirpath('conftest.py').copy(tmpdir.join('conftest.py'))
    xtxt = tmpdir.join('y.txt')
    xtxt.write(py.code.Source("""
        hello::
            .. >>> raise ValueError 
               >>> None
    """))
    config = py.test.config._reparse([xtxt]) 
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(Failed) 
    assert len(l) == 1

def test_doctest_basic(): 
    # XXX get rid of the next line: 
    py.magic.autopath().dirpath('conftest.py').copy(tmpdir.join('conftest.py'))

    xtxt = tmpdir.join('x.txt')
    xtxt.write(py.code.Source("""
        .. 
           >>> from os.path import abspath 

        hello world 

           >>> assert abspath 
           >>> i=3
           >>> print i
           3

        yes yes

            >>> i
            3

        end
    """))
    config = py.test.config._reparse([xtxt]) 
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(Failed)
    assert len(l) == 0 
    l = session.getitemoutcomepairs(Passed)
    l2 = session.getitemoutcomepairs(Skipped)
    assert len(l+l2) == 2

def test_deindent():
    from py.__.doc.conftest import deindent
    assert deindent('foo') == 'foo'
    assert deindent('foo\n  bar') == 'foo\n  bar'
    assert deindent('  foo\n  bar\n') == 'foo\nbar\n'
    assert deindent('  foo\n\n  bar\n') == 'foo\n\nbar\n'
    assert deindent(' foo\n  bar\n') == 'foo\n bar\n'
    assert deindent('  foo\n bar\n') == ' foo\nbar\n'

def test_doctest_eol(): 
    # XXX get rid of the next line: 
    py.magic.autopath().dirpath('conftest.py').copy(tmpdir.join('conftest.py'))

    ytxt = tmpdir.join('y.txt')
    ytxt.write(py.code.Source(".. >>> 1 + 1\r\n   2\r\n\r\n"))
    config = py.test.config._reparse([ytxt]) 
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(Failed)
    assert len(l) == 0 
    l = session.getitemoutcomepairs(Passed)
    l2 = session.getitemoutcomepairs(Skipped)
    assert len(l+l2) == 2

def test_doctest_indentation():
    # XXX get rid of the next line: 
    py.magic.autopath().dirpath('conftest.py').copy(tmpdir.join('conftest.py'))

    txt = tmpdir.join('foo.txt')
    txt.write('..\n  >>> print "foo\\n  bar"\n  foo\n    bar\n')
    config = py.test.config._reparse([txt])
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(Failed)
    assert len(l) == 0
    l = session.getitemoutcomepairs(Passed)
    l2 = session.getitemoutcomepairs(Skipped)
    assert len(l+l2) == 2

def test_js_ignore():
    py.magic.autopath().dirpath('conftest.py').copy(tmpdir.join('conftest.py'))
    tmpdir.ensure('__init__.py')
    xtxt = tmpdir.join('x.txt')
    xtxt.write(py.code.Source("""
    `blah`_

    .. _`blah`: javascript:some_function()
    """))
    config = py.test.config._reparse([xtxt]) 
    session = config.initsession()
    session.main()
    l = session.getitemoutcomepairs(Failed)
    assert len(l) == 0 
    l = session.getitemoutcomepairs(Passed)
    l2 = session.getitemoutcomepairs(Skipped)
    assert len(l+l2) == 3

def test_resolve_linkrole():
    from py.__.doc.conftest import get_apigen_relpath
    apigen_relpath = get_apigen_relpath()
    from py.__.doc.conftest import resolve_linkrole
    assert resolve_linkrole('api', 'py.foo.bar', False) == (
        'py.foo.bar', apigen_relpath + 'api/foo.bar.html')
    assert resolve_linkrole('api', 'py.foo.bar()', False) == (
        'py.foo.bar()', apigen_relpath + 'api/foo.bar.html')
    assert resolve_linkrole('api', 'py', False) == (
        'py', apigen_relpath + 'api/index.html')
    py.test.raises(AssertionError, 'resolve_linkrole("api", "foo.bar")')
    assert resolve_linkrole('source', 'py/foo/bar.py', False) == (
        'py/foo/bar.py', apigen_relpath + 'source/foo/bar.py.html')
    assert resolve_linkrole('source', 'py/foo/', False) == (
        'py/foo/', apigen_relpath + 'source/foo/index.html')
    assert resolve_linkrole('source', 'py/', False) == (
        'py/', apigen_relpath + 'source/index.html')
    py.test.raises(AssertionError, 'resolve_linkrole("source", "/foo/bar/")')

def test_resolve_linkrole_check_api():
    from py.__.doc.conftest import resolve_linkrole
    assert resolve_linkrole('api', 'py.test.ensuretemp')
    py.test.raises(AssertionError, "resolve_linkrole('api', 'py.foo.baz')")

def test_resolve_linkrole_check_source():
    from py.__.doc.conftest import resolve_linkrole
    assert resolve_linkrole('source', 'py/path/common.py')
    py.test.raises(AssertionError,
                   "resolve_linkrole('source', 'py/foo/bar.py')")

