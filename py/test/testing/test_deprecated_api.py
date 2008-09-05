
import py
from py.__.test.testing import suptest

class TestCollectDeprecated(suptest.InlineCollection):
    def test_directory_run_join_warnings(self):
        p = self.makepyfile(test_one="")
        config = self.parseconfig()  
        dirnode = config.getfsnode(p.dirpath())
        py.test.deprecated_call(dirnode.run)
        # XXX for directories we still have join()
        #py.test.deprecated_call(dirnode.join, 'test_one')
        
    def test_collect_with_deprecated_run_and_join(self):
        self.makepyfile(conftest="""
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
            Directory = MyDirectory
        """)
        p = self.makepyfile(somefile="""
            def check(): pass
            class Cls:
                def check2(self): pass 
        """)
        config = self.parseconfig()
        dirnode = config.getfsnode(p.dirpath())
        colitems = py.test.deprecated_call(dirnode.collect)
        assert len(colitems) == 1
        modcol = colitems[0]
        assert modcol.name == "somefile.py"
        colitems = py.test.deprecated_call(modcol.collect)
        assert len(colitems) == 2
        assert colitems[0].name == 'check'
        assert colitems[1].name == 'Cls'
        clscol = colitems[1] 
        colitems = py.test.deprecated_call(clscol.collect)
        assert len(colitems) == 1
        icol = colitems[0] 
        colitems = py.test.deprecated_call(icol.collect)
        assert len(colitems) == 1
        assert colitems[0].name == 'check2'

    def test_collect_with_deprecated_join_but_no_run(self):
        self.makepyfile(conftest="""
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
        col = self.getmodulecol("""
            def somefunc(): pass
            def check_one(): pass
            class SomeClass: pass
        """)
        colitems = py.test.deprecated_call(col.collect)
        assert len(colitems) == 1
        funcitem = colitems[0]
        assert funcitem.name == "check_one"

    def test_function_custom_run(self):
        self.makepyfile(conftest="""
            import py
            class MyFunction(py.test.collect.Function):
                def run(self):
                    pass
            Function=MyFunction 
        """)
        modcol = self.getmodulecol("def test_func(): pass")
        funcitem = modcol.collect()[0]
        assert funcitem.name == 'test_func'
        py.test.deprecated_call(funcitem.runtest)

    def test_function_custom_execute(self):
        self.makepyfile(conftest="""
            import py
            class MyFunction(py.test.collect.Function):
                def execute(self, obj, *args):
                    pass
            Function=MyFunction 
        """)
        modcol = self.getmodulecol("def test_func(): pass")
        funcitem = modcol.collect()[0]
        assert funcitem.name == 'test_func'
        py.test.deprecated_call(funcitem.runtest)

    def test_function_deprecated_run_execute(self):
        modcol = self.getmodulecol("def test_some(): pass")
        funcitem = modcol.collect()[0]
        py.test.deprecated_call(funcitem.run)
        py.test.deprecated_call(funcitem.execute, funcitem.obj)

    def test_function_deprecated_run_recursive(self):
        self.makepyfile(conftest="""
            import py
            class Module(py.test.collect.Module):
                def run(self):
                    return super(Module, self).run()
        """)
        modcol = self.getmodulecol("def test_some(): pass")
        colitems = py.test.deprecated_call(modcol.collect)
        funcitem = colitems[0]

    def test_conftest_subclasses_Module_with_non_pyfile(self):
        self.makepyfile(conftest="""
            import py
            class Module(py.test.collect.Module):
                def run(self):
                    return []
            class Directory(py.test.collect.Directory):
                def consider_file(self, path, usefilters=True):
                    if path.basename == "testme.xxx":
                        return Module(path, parent=self)
                    return super(Directory, self).consider_file(path, usefilters=usefilters)
        """)
        testme = self._makefile('xxx', testme="hello")
        config = self.parseconfig(testme)
        col = config.getfsnode(testme)
        assert col.collect() == []
