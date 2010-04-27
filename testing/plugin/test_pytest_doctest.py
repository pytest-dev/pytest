from py._plugin.pytest_doctest import DoctestModule, DoctestTextfile

pytest_plugins = ["pytest_doctest"]

class TestDoctests:
 
    def test_collect_testtextfile(self, testdir):
        testdir.maketxtfile(whatever="")
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

    def test_collect_module(self, testdir):
        path = testdir.makepyfile(whatever="#")
        for p in (path, testdir.tmpdir): 
            items, reprec = testdir.inline_genitems(p, 
                '--doctest-modules')
            assert len(items) == 1
            assert isinstance(items[0], DoctestModule)

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
        p = testdir.maketxtfile("""
            >>> i = 0
            >>> i = 1 
            >>> x
            2
        """)
        reprec = testdir.inline_run(p)
        call = reprec.getcall("pytest_runtest_logreport")
        assert call.report.failed
        assert call.report.longrepr 
        # XXX 
        #testitem, = items
        #excinfo = py.test.raises(Failed, "testitem.runtest()")
        #repr = testitem.repr_failure(excinfo, ("", ""))
        #assert repr.reprlocation 

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

    def test_doctestmodule_external(self, testdir):
        p = testdir.makepyfile("""
            #
            def somefunc():
                '''
                    >>> i = 0
                    >>> i + 1
                    2
                '''
        """)
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
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            '001 >>> i = 0',
            '002 >>> i + 1',
            'Expected:',
            "    2",
            "Got:",
            "    1",
            "*test_txtfile_failing.txt:2: DocTestFailure"
        ])
