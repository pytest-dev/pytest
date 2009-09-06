
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
        
