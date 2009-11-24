from py.plugin.pytest_restdoc import deindent

def test_deindent():
    assert deindent('foo') == 'foo'
    assert deindent('foo\n  bar') == 'foo\n  bar'
    assert deindent('  foo\n  bar\n') == 'foo\nbar\n'
    assert deindent('  foo\n\n  bar\n') == 'foo\n\nbar\n'
    assert deindent(' foo\n  bar\n') == 'foo\n bar\n'
    assert deindent('  foo\n bar\n') == ' foo\nbar\n'

class TestApigenLinkRole:
    disabled = True

    # these tests are moved here from the former py/doc/conftest.py
    def test_resolve_linkrole(self):
        from py.impl.doc.conftest import get_apigen_relpath
        apigen_relpath = get_apigen_relpath()

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

    def test_resolve_linkrole_check_api(self):
        assert resolve_linkrole('api', 'py.test.ensuretemp')
        py.test.raises(AssertionError, "resolve_linkrole('api', 'py.foo.baz')")

    def test_resolve_linkrole_check_source(self):
        assert resolve_linkrole('source', 'py/path/common.py')
        py.test.raises(AssertionError,
                       "resolve_linkrole('source', 'py/foo/bar.py')")


class TestDoctest:
    def pytest_funcarg__testdir(self, request):
        testdir = request.getfuncargvalue("testdir")
        assert request.module.__name__ == __name__
        testdir.makepyfile(confrest=
            "from py.plugin.pytest_restdoc import Project")
        # we scope our confrest file so that it doesn't
        # conflict with another global confrest.py 
        testdir.makepyfile(__init__="")
        for p in testdir.plugins:
            if p == globals():
                break
        else:
            testdir.plugins.append(globals())
        return testdir
    
    def test_doctest_extra_exec(self, testdir):
        xtxt = testdir.maketxtfile(x="""
            hello::
                .. >>> raise ValueError 
                   >>> None
        """)
        reprec = testdir.inline_run(xtxt)
        passed, skipped, failed = reprec.countoutcomes()
        assert failed == 1

    def test_doctest_basic(self, testdir): 
        xtxt = testdir.maketxtfile(x="""
            .. 
               >>> from os.path import abspath 

            hello world 

               >>> assert abspath 
               >>> i=3
               >>> print (i)
               3

            yes yes

                >>> i
                3

            end
        """)
        reprec = testdir.inline_run(xtxt)
        passed, skipped, failed = reprec.countoutcomes()
        assert failed == 0 
        assert passed + skipped == 2

    def test_doctest_eol(self, testdir): 
        ytxt = testdir.maketxtfile(y=".. >>> 1 + 1\r\n   2\r\n\r\n")
        reprec = testdir.inline_run(ytxt)
        passed, skipped, failed = reprec.countoutcomes()
        assert failed == 0 
        assert passed + skipped == 2

    def test_doctest_indentation(self, testdir):
        footxt = testdir.maketxtfile(foo=
            '..\n  >>> print ("foo\\n  bar")\n  foo\n    bar\n')
        reprec = testdir.inline_run(footxt)
        passed, skipped, failed = reprec.countoutcomes()
        assert failed == 0
        assert skipped + passed == 2 

    def test_js_ignore(self, testdir):
        xtxt = testdir.maketxtfile(xtxt="""
            `blah`_

            .. _`blah`: javascript:some_function()
        """)
        reprec = testdir.inline_run(xtxt)
        passed, skipped, failed = reprec.countoutcomes()
        assert failed == 0
        assert skipped + passed == 3 

    def test_pytest_doctest_prepare_content(self, testdir):
        l = []
        class MyPlugin:
            def pytest_doctest_prepare_content(self, content):
                l.append(content)
                return content.replace("False", "True")

        testdir.plugins.append(MyPlugin())

        xtxt = testdir.maketxtfile(x="""
            hello:

                >>> 2 == 2
                False

        """)
        reprec = testdir.inline_run(xtxt)
        assert len(l) == 1
        passed, skipped, failed = reprec.countoutcomes()
        assert passed >= 1
        assert not failed 
        assert skipped <= 1
