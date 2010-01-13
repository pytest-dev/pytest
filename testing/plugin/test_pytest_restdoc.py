import py
from py._plugin.pytest_restdoc import deindent

def test_deindent():
    assert deindent('foo') == 'foo'
    assert deindent('foo\n  bar') == 'foo\n  bar'
    assert deindent('  foo\n  bar\n') == 'foo\nbar\n'
    assert deindent('  foo\n\n  bar\n') == 'foo\n\nbar\n'
    assert deindent(' foo\n  bar\n') == 'foo\n bar\n'
    assert deindent('  foo\n bar\n') == ' foo\nbar\n'

class TestDoctest:
    def setup_class(cls):
        py.test.importorskip("docutils")

    def pytest_funcarg__testdir(self, request):
        testdir = request.getfuncargvalue("testdir")
        testdir.plugins.append("restdoc")
        assert request.module.__name__ == __name__
        testdir.makepyfile(confrest=
            "from py._plugin.pytest_restdoc import Project")
        # we scope our confrest file so that it doesn't
        # conflict with another global confrest.py 
        testdir.makepyfile(__init__="")
        return testdir
    
    def test_doctest_extra_exec(self, testdir):
        xtxt = testdir.maketxtfile(x="""
            hello::
                .. >>> raise ValueError 
                   >>> None
        """)
        result = testdir.runpytest(xtxt)
        result.stdout.fnmatch_lines(['*1 fail*'])

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
        result = testdir.runpytest(xtxt)
        result.stdout.fnmatch_lines([
            "*2 passed*"
        ])

    def test_doctest_eol(self, testdir): 
        ytxt = testdir.maketxtfile(y=".. >>> 1 + 1\r\n   2\r\n\r\n")
        result = testdir.runpytest(ytxt)
        result.stdout.fnmatch_lines(["*2 passed*"])

    def test_doctest_indentation(self, testdir):
        footxt = testdir.maketxtfile(foo=
            '..\n  >>> print ("foo\\n  bar")\n  foo\n    bar\n')
        result = testdir.runpytest(footxt)
        result.stdout.fnmatch_lines(["*2 passed*"])

    def test_js_ignore(self, testdir):
        xtxt = testdir.maketxtfile(xtxt="""
            `blah`_

            .. _`blah`: javascript:some_function()
        """)
        result = testdir.runpytest(xtxt)
        result.stdout.fnmatch_lines(["*3 passed*"])

    def test_pytest_doctest_prepare_content(self, testdir):
        testdir.makeconftest("""
            def pytest_doctest_prepare_content(content):
                return content.replace("False", "True")
        """)
        xtxt = testdir.maketxtfile(x="""
            hello:

                >>> 2 == 2
                False

        """)
        result = testdir.runpytest(xtxt)
        outcomes = result.parseoutcomes()
        assert outcomes['passed'] >= 1
        assert 'failed' not in outcomes
        assert 'skipped' not in outcomes 
