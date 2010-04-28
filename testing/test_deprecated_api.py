
import py

class TestCollectDeprecated:
        
    def test_collect_with_deprecated_run_and_join(self, testdir, recwarn):
        testdir.makeconftest("""
            import py

            class MyInstance(py.test.collect.Instance):
                def run(self):
                    return ['check2']
                def join(self, name):
                    if name == 'check2':
                        return self.Function(name=name, parent=self)

            class MyClass(py.test.collect.Class):
                def run(self):
                    return ['check2']
                def join(self, name):
                    return MyInstance(name='i', parent=self)

            class MyModule(py.test.collect.Module):
                def run(self):
                    return ['check', 'Cls']
                def join(self, name):
                    if name == 'check':
                        return self.Function(name, parent=self)
                    if name == 'Cls':
                        return MyClass(name, parent=self)
            
            class MyDirectory(py.test.collect.Directory):
                Module = MyModule
                def run(self):
                    return ['somefile.py']
                def join(self, name):
                    if name == "somefile.py":
                        return self.Module(self.fspath.join(name), parent=self)

            def pytest_collect_directory(path, parent):
                if path.basename == "subconf": 
                    return MyDirectory(path, parent)
        """)
        subconf = testdir.mkpydir("subconf")
        somefile = subconf.join("somefile.py")
        somefile.write(py.code.Source("""
            def check(): pass
            class Cls:
                def check2(self): pass 
        """))
        config = testdir.parseconfig(somefile)
        dirnode = config.getnode(somefile.dirpath())
        colitems = dirnode.collect()
        w = recwarn.pop(DeprecationWarning)
        assert w.filename.find("conftest.py") != -1
        #recwarn.resetregistry()
        #assert 0, (w.message, w.filename, w.lineno)
        assert len(colitems) == 1
        modcol = colitems[0]
        assert modcol.name == "somefile.py"
        colitems = modcol.collect()
        recwarn.pop(DeprecationWarning)
        assert len(colitems) == 2
        assert colitems[0].name == 'check'
        assert colitems[1].name == 'Cls'
        clscol = colitems[1] 

        colitems = clscol.collect()
        recwarn.pop(DeprecationWarning)
        assert len(colitems) == 1
        icol = colitems[0] 
        colitems = icol.collect()
        recwarn.pop(DeprecationWarning)
        assert len(colitems) == 1
        assert colitems[0].name == 'check2'

    def test_collect_with_deprecated_join_but_no_run(self, testdir, recwarn):
        testdir.makepyfile(conftest="""
            import py

            class Module(py.test.collect.Module):
                def funcnamefilter(self, name):
                    if name.startswith("check_"):
                        return True
                    return super(Module, self).funcnamefilter(name)
                def join(self, name):
                    if name.startswith("check_"):
                        return self.Function(name, parent=self)
                    assert name != "SomeClass", "join should not be called with this name"
        """)
        col = testdir.getmodulecol("""
            def somefunc(): pass
            def check_one(): pass
            class SomeClass: pass
        """)
        colitems = col.collect()
        recwarn.pop(DeprecationWarning) 
        assert len(colitems) == 1
        funcitem = colitems[0]
        assert funcitem.name == "check_one"

    def test_function_custom_run(self, testdir, recwarn):
        testdir.makepyfile(conftest="""
            import py
            class Function(py.test.collect.Function):
                def run(self):
                    pass
        """)
        modcol = testdir.getmodulecol("def test_func(): pass")
        funcitem = modcol.collect()[0]
        assert funcitem.name == 'test_func'
        recwarn.clear()
        funcitem._deprecated_testexecution()
        recwarn.pop(DeprecationWarning)

    def test_function_custom_execute(self, testdir, recwarn):
        testdir.makepyfile(conftest="""
            import py

            class MyFunction(py.test.collect.Function):
                def execute(self, obj, *args):
                    pass
            Function=MyFunction 
        """)
        modcol = testdir.getmodulecol("def test_func2(): pass")
        funcitem = modcol.collect()[0]
        w = recwarn.pop(DeprecationWarning) # for defining conftest.Function
        assert funcitem.name == 'test_func2'
        funcitem._deprecated_testexecution()
        w = recwarn.pop(DeprecationWarning)
        assert w.filename.find("conftest.py") != -1

    def test_function_deprecated_run_execute(self, testdir, recwarn):
        testdir.makepyfile(conftest="""
            import py

            class Function(py.test.collect.Function):

                def run(self):
                    pass
        """)
        modcol = testdir.getmodulecol("def test_some2(): pass")
        funcitem = modcol.collect()[0]
        w = recwarn.pop(DeprecationWarning)
        assert "conftest.py" in str(w.message) 

        recwarn.clear()
        funcitem._deprecated_testexecution()
        recwarn.pop(DeprecationWarning)

    def test_function_deprecated_run_recursive(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class Module(py.test.collect.Module):
                def run(self):
                    return super(Module, self).run()
        """)
        modcol = testdir.getmodulecol("def test_some(): pass")
        colitems = py.test.deprecated_call(modcol.collect)
        funcitem = colitems[0]

    def test_conftest_subclasses_Module_with_non_pyfile(self, testdir):
        testdir.makepyfile(conftest="""
            import py
            class Module(py.test.collect.Module):
                def run(self):
                    return []
            class Directory(py.test.collect.Directory):
                def consider_file(self, path):
                    if path.basename == "testme.xxx":
                        return Module(path, parent=self)
                    return super(Directory, self).consider_file(path)
        """)
        testme = testdir.makefile('xxx', testme="hello")
        config = testdir.parseconfig(testme)
        col = config.getnode(testme)
        assert col.collect() == []


    
class TestDisabled:
    def test_disabled_module(self, recwarn, testdir):
        modcol = testdir.getmodulecol("""
            disabled = True
            def setup_module(mod):
                raise ValueError
            def test_method():
                pass
        """)
        l = modcol.collect()
        assert len(l) == 1
        recwarn.clear()
        py.test.raises(py.test.skip.Exception, "modcol.setup()")
        recwarn.pop(DeprecationWarning)

    def test_disabled_class(self, recwarn, testdir):
        modcol = testdir.getmodulecol("""
            class TestClass:
                disabled = True
                def test_method(self):
                    pass
        """)
        l = modcol.collect()
        assert len(l) == 1
        modcol = l[0]
        assert isinstance(modcol, py.test.collect.Class)
        l = modcol.collect()
        assert len(l) == 1
        recwarn.clear()
        py.test.raises(py.test.skip.Exception, "modcol.setup()")
        recwarn.pop(DeprecationWarning)

    def test_disabled_class_functional(self, testdir):
        reprec = testdir.inline_runsource("""
            class TestSimpleClassSetup:
                disabled = True
                def test_classlevel(self): pass
                def test_classlevel2(self): pass
        """)
        reprec.assertoutcome(skipped=2)

    @py.test.mark.multi(name="Directory Module Class Function".split())
    def test_function_deprecated_run_execute(self, name, testdir, recwarn):
        testdir.makeconftest("""
            import py
            class %s(py.test.collect.%s):
                pass
        """ % (name, name))
        p = testdir.makepyfile("""
            class TestClass:
                def test_method(self):
                    pass
            def test_function():
                pass
        """)
        config = testdir.parseconfig()
        if name == "Directory":
            config.getnode(testdir.tmpdir)
        elif name in ("Module", "File"):
            config.getnode(p)
        else:
            fnode = config.getnode(p) 
            recwarn.clear()
            fnode.collect()
        w = recwarn.pop(DeprecationWarning)
        assert "conftest.py" in str(w.message)

def test_config_cmdline_options(recwarn, testdir):
    testdir.makepyfile(conftest="""
        import py
        def _callback(option, opt_str, value, parser, *args, **kwargs):
            option.tdest = True
        Option = py.test.config.Option
        option = py.test.config.addoptions("testing group", 
            Option('-G', '--glong', action="store", default=42,
                   type="int", dest="gdest", help="g value."), 
            # XXX note: special case, option without a destination
            Option('-T', '--tlong', action="callback", callback=_callback,
                    help='t value'),
            )
        """)
    recwarn.clear()
    config = testdir.reparseconfig(['-G', '17'])
    recwarn.pop(DeprecationWarning)
    assert config.option.gdest == 17 

def test_conftest_non_python_items(recwarn, testdir):
    testdir.makepyfile(conftest="""
        import py
        class CustomItem(py.test.collect.Item): 
            def run(self):
                pass
        class Directory(py.test.collect.Directory):
            def consider_file(self, fspath):
                if fspath.ext == ".xxx":
                    return CustomItem(fspath.basename, parent=self)
    """)
    checkfile = testdir.makefile(ext="xxx", hello="world")
    testdir.makepyfile(x="")
    testdir.maketxtfile(x="")
    config = testdir.parseconfig()
    recwarn.clear()
    dircol = config.getnode(checkfile.dirpath())
    w = recwarn.pop(DeprecationWarning)
    assert str(w.message).find("conftest.py") != -1
    colitems = dircol.collect()
    assert len(colitems) == 1
    assert colitems[0].name == "hello.xxx"
    assert colitems[0].__class__.__name__ == "CustomItem"

    item = config.getnode(checkfile)
    assert item.name == "hello.xxx"
    assert item.__class__.__name__ == "CustomItem"

def test_extra_python_files_and_functions(testdir):
    testdir.makepyfile(conftest="""
        import py
        class MyFunction(py.test.collect.Function):
            pass
        class Directory(py.test.collect.Directory):
            def consider_file(self, path):
                if path.check(fnmatch="check_*.py"):
                    return self.Module(path, parent=self)
                return super(Directory, self).consider_file(path)
        class myfuncmixin: 
            Function = MyFunction
            def funcnamefilter(self, name): 
                return name.startswith('check_') 
        class Module(myfuncmixin, py.test.collect.Module):
            def classnamefilter(self, name): 
                return name.startswith('CustomTestClass') 
        class Instance(myfuncmixin, py.test.collect.Instance):
            pass 
    """)
    checkfile = testdir.makepyfile(check_file="""
        def check_func():
            assert 42 == 42
        class CustomTestClass:
            def check_method(self):
                assert 23 == 23
    """)
    # check that directory collects "check_" files 
    config = testdir.parseconfig()
    col = config.getnode(checkfile.dirpath())
    colitems = col.collect()
    assert len(colitems) == 1
    assert isinstance(colitems[0], py.test.collect.Module)

    # check that module collects "check_" functions and methods
    config = testdir.parseconfig(checkfile)
    col = config.getnode(checkfile)
    assert isinstance(col, py.test.collect.Module)
    colitems = col.collect()
    assert len(colitems) == 2
    funccol = colitems[0]
    assert isinstance(funccol, py.test.collect.Function)
    assert funccol.name == "check_func"
    clscol = colitems[1]
    assert isinstance(clscol, py.test.collect.Class)
    colitems = clscol.collect()[0].collect()
    assert len(colitems) == 1
    assert colitems[0].name == "check_method"

