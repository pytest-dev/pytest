import sys, py

pytest_plugins = "pytest_pytester"

@py.test.mark.multi(name=[x for x in dir(py.cmdline) if x[0] != "_"])
def test_cmdmain(name, pytestconfig):
    main = getattr(py.cmdline, name)
    assert py.builtin.callable(main)
    assert name[:2] == "py"
    if pytestconfig.getvalue("toolsonpath"):
        scriptname = "py." + name[2:]
        assert py.path.local.sysfind(scriptname), scriptname

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

class TestPyCleanup:
    def test_basic(self, testdir, tmpdir):
        p = tmpdir.ensure("hello.py")
        result = testdir.runpybin("py.cleanup", tmpdir)
        assert result.ret == 0
        assert p.check()
        pyc = p.new(ext='pyc')
        pyc.ensure()
        result = testdir.runpybin("py.cleanup", tmpdir)
        assert not pyc.check()

    def test_dir_remove_simple(self, testdir, tmpdir):
        subdir = tmpdir.mkdir("subdir")
        p = subdir.ensure("file")
        result = testdir.runpybin("py.cleanup", "-d", tmpdir)
        assert result.ret == 0
        assert subdir.check()
        p.remove()
        p = tmpdir.mkdir("hello")
        result = testdir.runpybin("py.cleanup", tmpdir, '-d')
        assert result.ret == 0
        assert not subdir.check()
