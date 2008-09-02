
import py
from py.__.test import event
from py.__.test.testing import suptest
from py.__.doc import conftest as doc_conftest


class TestDoctest(suptest.InlineCollection):
    def setup_method(self, method):
        super(TestDoctest, self).setup_method(method)
        p = py.path.local(doc_conftest.__file__)  
        if p.ext == ".pyc": 
            p = p.new(ext=".py")
        p.copy(self.tmpdir.join("conftest.py"))
    
    def test_doctest_extra_exec(self): 
        xtxt = self.maketxtfile(x="""
            hello::
                .. >>> raise ValueError 
                   >>> None
        """)
        sorter = suptest.events_from_cmdline([xtxt])
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 1

    def test_doctest_basic(self): 
        xtxt = self.maketxtfile(x="""
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
        """)
        sorter = suptest.events_from_cmdline([xtxt])
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 0 
        assert passed + skipped == 2

    def test_doctest_eol(self): 
        ytxt = self.maketxtfile(y=".. >>> 1 + 1\r\n   2\r\n\r\n")
        sorter = suptest.events_from_cmdline([ytxt])
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 0 
        assert passed + skipped == 2

    def test_doctest_indentation(self):
        footxt = self.maketxtfile(foo=
            '..\n  >>> print "foo\\n  bar"\n  foo\n    bar\n')
        sorter = suptest.events_from_cmdline([footxt])
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 0
        assert skipped + passed == 2 

    def test_js_ignore(self):
        xtxt = self.maketxtfile(xtxt="""
            `blah`_

            .. _`blah`: javascript:some_function()
        """)
        sorter = suptest.events_from_cmdline([xtxt])
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 0
        assert skipped + passed == 3 

def test_deindent():
    deindent = doc_conftest.deindent
    assert deindent('foo') == 'foo'
    assert deindent('foo\n  bar') == 'foo\n  bar'
    assert deindent('  foo\n  bar\n') == 'foo\nbar\n'
    assert deindent('  foo\n\n  bar\n') == 'foo\n\nbar\n'
    assert deindent(' foo\n  bar\n') == 'foo\n bar\n'
    assert deindent('  foo\n bar\n') == ' foo\nbar\n'


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

