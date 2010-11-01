import sys, py

class TestGeneralUsage:
    def test_config_error(self, testdir):
        testdir.makeconftest("""
            def pytest_configure(config):
                import pytest
                raise pytest.UsageError("hello")
        """)
        result = testdir.runpytest(testdir.tmpdir)
        assert result.ret != 0
        result.stderr.fnmatch_lines([
            '*ERROR: hello'
        ])

    def test_file_not_found(self, testdir):
        result = testdir.runpytest("asd")
        assert result.ret != 0
        result.stderr.fnmatch_lines(["ERROR: file not found*asd"])

    def test_config_preparse_plugin_option(self, testdir):
        testdir.makepyfile(pytest_xyz="""
            def pytest_addoption(parser):
                parser.addoption("--xyz", dest="xyz", action="store")
        """)
        testdir.makepyfile(test_one="""
            import py
            def test_option(pytestconfig):
                assert pytestconfig.option.xyz == "123"
        """)
        result = testdir.runpytest("-p", "xyz", "--xyz=123")
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            '*1 passed*',
        ])

    def test_basetemp(self, testdir):
        mytemp = testdir.tmpdir.mkdir("mytemp")
        p = testdir.makepyfile("""
            import py
            def test_1(pytestconfig):
                pytestconfig.getbasetemp().ensure("hello")
        """)
        result = testdir.runpytest(p, '--basetemp=%s' %mytemp)
        assert result.ret == 0
        assert mytemp.join('hello').check()

    def test_assertion_magic(self, testdir):
        p = testdir.makepyfile("""
            def test_this():
                x = 0
                assert x
        """)
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            ">       assert x",
            "E       assert 0",
        ])
        assert result.ret == 1

    def test_nested_import_error(self, testdir):
        p = testdir.makepyfile("""
                import import_fails
                def test_this():
                    assert import_fails.a == 1
        """)
        testdir.makepyfile(import_fails="import does_not_work")
        result = testdir.runpytest(p)
        result.stdout.fnmatch_lines([
            #XXX on jython this fails:  ">   import import_fails",
            "E   ImportError: No module named does_not_work",
        ])
        assert result.ret == 1

    def test_not_collectable_arguments(self, testdir):
        p1 = testdir.makepyfile("")
        p2 = testdir.makefile(".pyc", "123")
        result = testdir.runpytest(p1, p2)
        assert result.ret != 0
        result.stderr.fnmatch_lines([
            "*ERROR: can't collect:*%s" %(p2.basename,)
        ])


    def test_earlyinit(self, testdir):
        p = testdir.makepyfile("""
            import py
            assert hasattr(py.test, 'mark')
        """)
        result = testdir.runpython(p)
        assert result.ret == 0

    def test_pydoc(self, testdir):
        result = testdir.runpython_c("import py;help(py.test)")
        assert result.ret == 0
        s = result.stdout.str()
        assert 'MarkGenerator' in s

    def test_double_pytestcmdline(self, testdir):
        p = testdir.makepyfile(run="""
            import py
            py.test.cmdline.main()
            py.test.cmdline.main()
        """)
        testdir.makepyfile("""
            def test_hello():
                pass
        """)
        result = testdir.runpython(p)
        result.stdout.fnmatch_lines([
            "*1 passed*",
            "*1 passed*",
        ])


    @py.test.mark.xfail
    def test_early_skip(self, testdir):
        testdir.mkdir("xyz")
        testdir.makeconftest("""
            import py
            def pytest_collect_directory():
                py.test.skip("early")
        """)
        result = testdir.runpytest()
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*1 skip*"
        ])


    def test_issue88_initial_file_multinodes(self, testdir):
        testdir.makeconftest("""
            import py
            class MyFile(py.test.collect.File):
                def collect(self):
                    return
            def pytest_collect_file(path, parent):
                return MyFile(path, parent)
        """)
        p = testdir.makepyfile("def test_hello(): pass")
        result = testdir.runpytest(p, "--collectonly")
        result.stdout.fnmatch_lines([
            "*MyFile*test_issue88*",
            "*Module*test_issue88*",
        ])

    def test_issue93_initialnode_importing_capturing(self, testdir):
        testdir.makeconftest("""
            import sys
            print ("should not be seen")
            sys.stderr.write("stder42\\n")
        """)
        result = testdir.runpytest()
        assert result.ret == 0
        assert "should not be seen" not in result.stdout.str()
        assert "stderr42" not in result.stderr.str()

    def test_conftest_printing_shows_if_error(self, testdir):
        testdir.makeconftest("""
            print ("should be seen")
            assert 0
        """)
        result = testdir.runpytest()
        assert result.ret != 0
        assert "should be seen" in result.stdout.str()

    @py.test.mark.skipif("not hasattr(os, 'symlink')")
    def test_chdir(self, testdir):
        testdir.tmpdir.join("py").mksymlinkto(py._pydir)
        p = testdir.tmpdir.join("main.py")
        p.write(py.code.Source("""
            import sys, os
            sys.path.insert(0, '')
            import py
            print (py.__file__)
            print (py.__path__)
            os.chdir(os.path.dirname(os.getcwd()))
            print (py.log.Producer)
        """))
        result = testdir.runpython(p, prepend=False)
        assert not result.ret

    def test_issue109_sibling_conftests_not_loaded(self, testdir):
        sub1 = testdir.tmpdir.mkdir("sub1")
        sub2 = testdir.tmpdir.mkdir("sub2")
        sub1.join("conftest.py").write("assert 0")
        result = testdir.runpytest(sub2)
        assert result.ret == 0
        sub2.ensure("__init__.py")
        p = sub2.ensure("test_hello.py")
        result = testdir.runpytest(p)
        assert result.ret == 0
        result = testdir.runpytest(sub1)
        assert result.ret != 0

    def test_directory_skipped(self, testdir):
        testdir.makeconftest("""
            import py
            def pytest_ignore_collect():
                py.test.skip("intentional")
        """)
        testdir.makepyfile("def test_hello(): pass")
        result = testdir.runpytest()
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*1 skipped*"
        ])

    def test_multiple_items_per_collector_byid(self, testdir):
        c = testdir.makeconftest("""
            import py
            class MyItem(py.test.collect.Item):
                def runtest(self):
                    pass
            class MyCollector(py.test.collect.File):
                def collect(self):
                    return [MyItem(name="xyz", parent=self)]
            def pytest_collect_file(path, parent):
                if path.basename.startswith("conftest"):
                    return MyCollector(path, parent)
        """)
        result = testdir.runpytest(c.basename+"::"+"xyz")
        assert result.ret == 0
        result.stdout.fnmatch_lines([
            "*1 pass*",
        ])


    @py.test.mark.skipif("sys.version_info < (2,5)")
    def test_python_minus_m_invocation_ok(self, testdir):
        p1 = testdir.makepyfile("def test_hello(): pass")
        res = testdir.run(py.std.sys.executable, "-m", "py.test", str(p1))
        assert res.ret == 0

    @py.test.mark.skipif("sys.version_info < (2,5)")
    def test_python_minus_m_invocation_fail(self, testdir):
        p1 = testdir.makepyfile("def test_fail(): 0/0")
        res = testdir.run(py.std.sys.executable, "-m", "py.test", str(p1))
        assert res.ret == 1

    def test_skip_on_generated_funcarg_id(self, testdir):
        testdir.makeconftest("""
            import py
            def pytest_generate_tests(metafunc):
                metafunc.addcall({'x': 3}, id='hello-123')
            def pytest_runtest_setup(item):
                print (item.keywords)
                if 'hello-123' in item.keywords:
                    py.test.skip("hello")
                assert 0
        """)
        p = testdir.makepyfile("""def test_func(x): pass""")
        res = testdir.runpytest(p)
        assert res.ret == 0
        res.stdout.fnmatch_lines(["*1 skipped*"])
