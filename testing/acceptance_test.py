import sys, py

class TestGeneralUsage:
    def test_config_error(self, testdir):
        testdir.makeconftest("""
            def pytest_configure(config):
                raise config.Error("hello")
        """)
        result = testdir.runpytest(testdir.tmpdir)
        assert result.ret != 0
        result.stderr.fnmatch_lines([
            '*ERROR: hello'
        ])

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
            "*ERROR: can't collect: %s" %(p2,)
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
           

    @py.test.mark.xfail
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

    @py.test.mark.xfail
    def test_issue93_initialnode_importing_capturing(self, testdir):
        testdir.makeconftest("""
            print "should not be seen"
        """)
        result = testdir.runpytest()
        assert result.ret == 0
        assert "should not be seen" not in result.stdout.str()
