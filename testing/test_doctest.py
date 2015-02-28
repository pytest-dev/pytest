from _pytest.doctest import DoctestItem, DoctestModule, DoctestTextfile
import py, pytest

class TestDoctests:

    def test_collect_testtextfile(self, testdir):
        w = testdir.maketxtfile(whatever="")
        checkfile = testdir.maketxtfile(test_something="""
            alskdjalsdk
            >>> i = 5
            >>> i-1
            4
        """)
        for x in (testdir.tmpdir, checkfile):
            #print "checking that %s returns custom items" % (x,)
            items, reprec = testdir.inline_genitems(x)
            assert len(items) == 1
            assert isinstance(items[0], DoctestTextfile)
        items, reprec = testdir.inline_genitems(w)
        assert len(items) == 1

    def test_collect_module_empty(self, testdir):
        path = testdir.makepyfile(whatever="#")
        for p in (path, testdir.tmpdir):
            items, reprec = testdir.inline_genitems(p,
                '--doctest-modules')
            assert len(items) == 0

    def test_collect_module_single_modulelevel_doctest(self, testdir):
        path = testdir.makepyfile(whatever='""">>> pass"""')
        for p in (path, testdir.tmpdir):
            items, reprec = testdir.inline_genitems(p,
                '--doctest-modules')
            assert len(items) == 1
            assert isinstance(items[0], DoctestItem)
            assert isinstance(items[0].parent, DoctestModule)

    def test_collect_module_two_doctest_one_modulelevel(self, testdir):
        path = testdir.makepyfile(whatever="""
            '>>> x = None'
            def my_func():
                ">>> magic = 42 "
        """)
        for p in (path, testdir.tmpdir):
            items, reprec = testdir.inline_genitems(p,
                '--doctest-modules')
            assert len(items) == 2
            assert isinstance(items[0], DoctestItem)
            assert isinstance(items[1], DoctestItem)
            assert isinstance(items[0].parent, DoctestModule)
            assert items[0].parent is items[1].parent

    def test_collect_module_two_doctest_no_modulelevel(self, testdir):
        path = testdir.makepyfile(whatever="""
            '# Empty'
            def my_func():
                ">>> magic = 42 "
            def unuseful():
                '''
                # This is a function
                # >>> # it doesn't have any doctest
                '''
            def another():
                '''
                # This is another function
                >>> import os # this one does have a doctest
                '''
        """)
        for p in (path, testdir.tmpdir):
            items, reprec = testdir.inline_genitems(p,
                '--doctest-modules')
            assert len(items) == 2
            assert isinstance(items[0], DoctestItem)
            assert isinstance(items[1], DoctestItem)
            assert isinstance(items[0].parent, DoctestModule)
            assert items[0].parent is items[1].parent

    @pytest.mark.xfail('hasattr(sys, "pypy_version_info")', reason=
                       "pypy leaks one FD")
    def test_simple_doctestfile(self, testdir):
        p = testdir.maketxtfile(test_doc="""
            >>> x = 1
            >>> x == 1
            False
        """)
        reprec = testdir.inline_run(p, )
        reprec.assertoutcome(failed=1)

    def test_new_pattern(self, testdir):
        p = testdir.maketxtfile(xdoc ="""
            >>> x = 1
            >>> x == 1
            False
        """)
        reprec = testdir.inline_run(p, "--doctest-glob=x*.txt")
        reprec.assertoutcome(failed=1)

    def test_doctest_unexpected_exception(self, testdir):
        testdir.maketxtfile("""
            >>> i = 0
            >>> 0 / i
            2
        """)
        result = testdir.runpytest("--doctest-modules")
        result.stdout.fnmatch_lines([
            "*unexpected_exception*",
            "*>>> i = 0*",
            "*>>> 0 / i*",
            "*UNEXPECTED*ZeroDivision*",
        ])

    def test_doctest_linedata_missing(self, testdir):
        testdir.tmpdir.join('hello.py').write(py.code.Source("""
            class Fun(object):
                @property
                def test(self):
                    '''
                    >>> a = 1
                    >>> 1/0
                    '''
            """))
        result = testdir.runpytest("--doctest-modules")
        result.stdout.fnmatch_lines([
            "*hello*",
            "*EXAMPLE LOCATION UNKNOWN, not showing all tests of that example*",
            "*1/0*",
            "*UNEXPECTED*ZeroDivision*",
            "*1 failed*",
        ])


    def test_doctest_unex_importerror(self, testdir):
        testdir.tmpdir.join("hello.py").write(py.code.Source("""
            import asdalsdkjaslkdjasd
        """))
        testdir.maketxtfile("""
            >>> import hello
            >>>
        """)
        result = testdir.runpytest("--doctest-modules")
        result.stdout.fnmatch_lines([
            "*>>> import hello",
            "*UNEXPECTED*ImportError*",
            "*import asdals*",
        ])

    def test_doctestmodule(self, testdir):
        p = testdir.makepyfile("""
            '''
                >>> x = 1
                >>> x == 1
                False

            '''
        """)
        reprec = testdir.inline_run(p, "--doctest-modules")
        reprec.assertoutcome(failed=1)

    def test_doctestmodule_external_and_issue116(self, testdir):
        p = testdir.mkpydir("hello")
        p.join("__init__.py").write(py.code.Source("""
            def somefunc():
                '''
                    >>> i = 0
                    >>> i + 1
                    2
                '''
        """))
        result = testdir.runpytest(p, "--doctest-modules")
        result.stdout.fnmatch_lines([
            '004 *>>> i = 0',
            '005 *>>> i + 1',
            '*Expected:',
            "*    2",
            "*Got:",
            "*    1",
            "*:5: DocTestFailure"
        ])


    def test_txtfile_failing(self, testdir):
        p = testdir.maketxtfile("""
            >>> i = 0
            >>> i + 1
            2
        """)
        result = testdir.runpytest(p, "-s")
        result.stdout.fnmatch_lines([
            '001 >>> i = 0',
            '002 >>> i + 1',
            'Expected:',
            "    2",
            "Got:",
            "    1",
            "*test_txtfile_failing.txt:2: DocTestFailure"
        ])

    def test_txtfile_with_fixtures(self, testdir):
        p = testdir.maketxtfile("""
            >>> dir = getfixture('tmpdir')
            >>> type(dir).__name__
            'LocalPath'
        """)
        reprec = testdir.inline_run(p, )
        reprec.assertoutcome(passed=1)

    def test_txtfile_with_usefixtures_in_ini(self, testdir):
        testdir.makeini("""
            [pytest]
            usefixtures = myfixture
        """)
        testdir.makeconftest("""
            import pytest
            @pytest.fixture
            def myfixture(monkeypatch):
                monkeypatch.setenv("HELLO", "WORLD")
        """)

        p = testdir.maketxtfile("""
            >>> import os
            >>> os.environ["HELLO"]
            'WORLD'
        """)
        reprec = testdir.inline_run(p, )
        reprec.assertoutcome(passed=1)

    def test_doctestmodule_with_fixtures(self, testdir):
        p = testdir.makepyfile("""
            '''
                >>> dir = getfixture('tmpdir')
                >>> type(dir).__name__
                'LocalPath'
            '''
        """)
        reprec = testdir.inline_run(p, "--doctest-modules")
        reprec.assertoutcome(passed=1)

    def test_doctestmodule_three_tests(self, testdir):
        p = testdir.makepyfile("""
            '''
            >>> dir = getfixture('tmpdir')
            >>> type(dir).__name__
            'LocalPath'
            '''
            def my_func():
                '''
                >>> magic = 42
                >>> magic - 42
                0
                '''
            def unuseful():
                pass
            def another():
                '''
                >>> import os
                >>> os is os
                True
                '''
        """)
        reprec = testdir.inline_run(p, "--doctest-modules")
        reprec.assertoutcome(passed=3)

    def test_doctestmodule_two_tests_one_fail(self, testdir):
        p = testdir.makepyfile("""
            class MyClass:
                def bad_meth(self):
                    '''
                    >>> magic = 42
                    >>> magic
                    0
                    '''
                def nice_meth(self):
                    '''
                    >>> magic = 42
                    >>> magic - 42
                    0
                    '''
        """)
        reprec = testdir.inline_run(p, "--doctest-modules")
        reprec.assertoutcome(failed=1, passed=1)

    def test_ignored_whitespace(self, testdir):
        testdir.makeini("""
            [pytest]
            doctest_optionflags = ELLIPSIS NORMALIZE_WHITESPACE
        """)
        p = testdir.makepyfile("""
            class MyClass:
                '''
                >>> a = "foo    "
                >>> print(a)
                foo
                '''
                pass
        """)
        reprec = testdir.inline_run(p, "--doctest-modules")
        reprec.assertoutcome(passed=1)

    def test_non_ignored_whitespace(self, testdir):
        testdir.makeini("""
            [pytest]
            doctest_optionflags = ELLIPSIS
        """)
        p = testdir.makepyfile("""
            class MyClass:
                '''
                >>> a = "foo    "
                >>> print(a)
                foo
                '''
                pass
        """)
        reprec = testdir.inline_run(p, "--doctest-modules")
        reprec.assertoutcome(failed=1, passed=0)

    def test_ignored_whitespace_glob(self, testdir):
        testdir.makeini("""
            [pytest]
            doctest_optionflags = ELLIPSIS NORMALIZE_WHITESPACE
        """)
        p = testdir.maketxtfile(xdoc="""
            >>> a = "foo    "
            >>> print(a)
            foo
        """)
        reprec = testdir.inline_run(p, "--doctest-glob=x*.txt")
        reprec.assertoutcome(passed=1)

    def test_non_ignored_whitespace_glob(self, testdir):
        testdir.makeini("""
            [pytest]
            doctest_optionflags = ELLIPSIS
        """)
        p = testdir.maketxtfile(xdoc="""
            >>> a = "foo    "
            >>> print(a)
            foo
        """)
        reprec = testdir.inline_run(p, "--doctest-glob=x*.txt")
        reprec.assertoutcome(failed=1, passed=0)

    def test_ignore_import_errors_on_doctest(self, testdir):
        p = testdir.makepyfile("""
            import asdf

            def add_one(x):
                '''
                >>> add_one(1)
                2
                '''
                return x + 1
        """)

        reprec = testdir.inline_run(p, "--doctest-modules",
                                    "--doctest-ignore-import-errors")
        reprec.assertoutcome(skipped=1, failed=1, passed=0)
