
pytest_plugins = "pytest_pytester"

class TestPyLookup:
    def test_basic(self, testdir):
        p = testdir.makepyfile(hello="def x(): pass")
        result = testdir.runpybin("py.lookup", "pass")
        result.stdout.fnmatch_lines(
            ['%s:*def x(): pass' %(p.basename)]
        )

    def test_search_in_filename(self, testdir):
        p = testdir.makepyfile(hello="def x(): pass")
        result = testdir.runpybin("py.lookup", "hello")
        result.stdout.fnmatch_lines(
            ['*%s:*' %(p.basename)]
        )

    def test_with_explicit_path(self, testdir):
        sub1 = testdir.mkdir("things")
        sub2 = testdir.mkdir("foo")
        sub1.join("pyfile.py").write("def stuff(): pass")
        searched = sub2.join("other.py")
        searched.write("stuff = x")
        result = testdir.runpybin("py.lookup", sub2.basename, "stuff")
        result.stdout.fnmatch_lines(
            ["%s:1: stuff = x" % (searched.basename,)]
        )
