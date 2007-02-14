
""" test doc generation
"""

import py
import sys

#try:
from py.__.apigen.tracer.tracer import Tracer
from py.__.apigen.tracer.docstorage import DocStorageAccessor, DocStorage, \
                                           get_star_import_tree, pkg_to_dict
from py.__.apigen.tracer.testing.runtest import cut_pyc
from py.__.apigen.tracer.description import FunctionDesc
from py.__.apigen.tracer import model
from py.__.apigen.tracer.permastore import PermaDocStorage

def setup_module(mod):
    if py.std.sys.platform == "win32":
        py.test.skip("tracing on win32 not supported") 

# XXX: Perma doc storage disabled a bit

sorted = py.builtin.sorted
set = py.builtin.set

def fun(a, b, c):
    "Some docstring"
    return "d"

def test_basic():
    descs = {"fun":fun}
    ds = DocStorage().from_dict(descs)
    t = Tracer(ds)
    t.start_tracing()
    fun(1, ("g", 3), 8)
    fun(2., ("a", 1.), "a")
    t.end_tracing()
    desc = ds.descs['fun']
    inputcells = desc.inputcells
    assert len(inputcells) == 3
    assert isinstance(inputcells[0], model.SomeUnion)
    assert isinstance(inputcells[1], model.SomeTuple)
    assert isinstance(inputcells[2], model.SomeUnion)
    assert isinstance(desc.retval, model.SomeString)
    cs = sorted(desc.call_sites.keys())
    assert len(cs) == 2
    f_name = cut_pyc(__file__)
    assert len(cs[0]) == 1
    assert len(cs[1]) == 1
    assert cs[1][0].filename == f_name
    # lines are counted from 0
    num = test_basic.func_code.co_firstlineno
    assert cs[1][0].lineno == num + 4 or cs[1][0].lineno == num + 5
    assert cs[0][0].filename == f_name
    assert cs[0][0].lineno == num + 5 or cs[0][0].lineno == num + 4
    if 0:
        pds = PermaDocStorage(DocStorageAccessor(ds))
        assert pds.get_function_names() == ['fun']
        sig = pds.get_function_signature('fun')
        assert sig[0][0][0] == 'a'
        assert isinstance(sig[0][0][1], model.SomeUnion)
        assert len(pds.get_function_callpoints('fun')) == 2

class AClass(object):
    """ Class docstring
    """
    def __init__(self, b="blah"):
        pass
    
    def exposed_method(self, a, b, c):
        """ method docstring
        """
        return self._hidden_method()
    
    def _hidden_method(self):
        """ should not appear
        """
        return "z"

class ANotherClass(AClass):
    def another_exposed_method(self, a):
        # no docstring
        return a

def test_class():
    descs = {'AClass':AClass}
    ds = DocStorage().from_dict(descs)
    t = Tracer(ds)
    t.start_tracing()
    s = AClass()
    s.exposed_method(1, 2., [1,2,3])
    t.end_tracing()
    desc = ds.descs['AClass']
    inputcells = desc.fields['__init__'].inputcells
    assert len(inputcells) == 2
    assert isinstance(inputcells[0], model.SomeInstance)
    #assert inputcells[0].classdef.classdesc.pyobj is SomeClass
    # XXX: should work
    assert isinstance(inputcells[1], model.SomeString)
    f_name = __file__
    if f_name.endswith('.pyc'):
        f_name = f_name[:-1]
    cs = sorted(desc.fields['__init__'].call_sites.keys())
    assert len(cs) == 1
    assert len(cs[0]) == 1
    assert cs[0][0].filename == f_name
    assert cs[0][0].lineno == test_class.func_code.co_firstlineno + 4
    # method check
    assert sorted(desc.getfields()) == ['__init__', 'exposed_method']
    inputcells = desc.fields['exposed_method'].inputcells
    assert len(inputcells) == 4
    assert isinstance(inputcells[0], model.SomeInstance)
    #assert inputcells[0].classdef.classdesc.pyobj is SomeClass
    # XXX should work
    assert isinstance(inputcells[1], model.SomeInt)
    assert isinstance(inputcells[2], model.SomeFloat)
    assert isinstance(inputcells[3], model.SomeList)
    assert isinstance(desc.fields['exposed_method'].retval, model.SomeString)
    if 0:
        pds = PermaDocStorage(DocStorageAccessor(ds))
        assert pds.get_class_names() == ['AClass']
        assert len(pds.get_function_signature('AClass.exposed_method')[0]) == 4

def other_fun():
    pass

def test_add_desc():
    ds = DocStorage().from_dict({})
    ds.add_desc("one", fun)
    ds.add_desc("one", other_fun)
    assert sorted(ds.descs.keys()) == ["one", "one_1"]
    assert isinstance(ds.descs["one"], FunctionDesc)
    assert isinstance(ds.descs["one_1"], FunctionDesc)
    assert ds.descs["one"].pyobj is fun
    assert ds.descs["one_1"].pyobj is other_fun
    assert ds.desc_cache[ds.descs["one"]] is ds.descs["one"]
    assert ds.desc_cache[ds.descs["one_1"]] is ds.descs["one_1"]

def test_while_call():
    ds = DocStorage().from_dict({"other_fun":other_fun})
    t = Tracer(ds)
    t.start_tracing()
    for x in xrange(8):
        other_fun()
    t.end_tracing()
    desc = ds.descs["other_fun"]
    assert len(desc.call_sites.keys()) == 1
    #assert isinstance(desc.call_sites.values()[0][0], py.code.Frame)
    if 0:
        pds = PermaDocStorage(DocStorageAccessor(ds))
        assert len(pds.get_function_callpoints("other_fun")) == 1

class A(object):
    def method(self, x):
        self.x = x

class B:
    def method(self, x):
        self.x = x

def test_without_init():
    ds = DocStorage().from_dict({'A':A, 'B':B})
    t = Tracer(ds)
    t.start_tracing()
    x = A()
    y = B()
    x.method(3)
    y.method(4)
    t.end_tracing()
    assert isinstance(ds.descs['A'].fields['method'].inputcells[1],
                      model.SomeInt)
    assert isinstance(ds.descs['B'].fields['method'].inputcells[1],
                      model.SomeInt)
    if 0:
        pds = PermaDocStorage(DocStorageAccessor(ds))

def test_local_changes():
    class testclass(object):
        def __init__(self):
            self.foo = 0
        def bar(self, x):
            self.foo = x
    ds = DocStorage().from_dict({'testclass': testclass})
    t = Tracer(ds)
    t.start_tracing()
    c = testclass()
    c.bar(1)
    t.end_tracing()
    desc = ds.descs['testclass']
    methdesc = desc.fields['bar']
    #assert methdesc.old_dict != methdesc.new_dict
    assert methdesc.get_local_changes() == {'foo': set(['changed'])}
    return ds

def test_local_changes_nochange():
    class testclass(object):
        def __init__(self):
            self.foo = 0
        def bar(self, x):
            self.foo = x
    ds = DocStorage().from_dict({'testclass': testclass})
    t = Tracer(ds)
    t.start_tracing()
    c = testclass()
    t.end_tracing()
    desc = ds.descs['testclass']
    methdesc = desc.fields['bar']
    assert methdesc.get_local_changes() == {}
    return ds

def test_multiple_classes_with_same_init():
    class A:
        def __init__(self, x):
            self.x = x
    
    class B(A):
        pass
    
    ds = DocStorage().from_dict({'A':A, 'B':B})
    t = Tracer(ds)
    t.start_tracing()
    c = A(3)
    d = B(4)
    t.end_tracing()
    assert len(ds.descs['A'].fields['__init__'].call_sites) == 1
    assert len(ds.descs['B'].fields['__init__'].call_sites) == 1
    return ds

def test_exception_raise():
    def x():
        1/0
    
    def y():
        try:
            x()
        except ZeroDivisionError:
            pass
    
    def z():
        y()
    
    ds = DocStorage().from_dict({'x':x, 'y':y, 'z':z})
    t = Tracer(ds)
    t.start_tracing()
    z()
    t.end_tracing()
    assert ds.descs['x'].exceptions.keys() == [ZeroDivisionError]
    assert ds.descs['y'].exceptions.keys() == [ZeroDivisionError]
    assert ds.descs['z'].exceptions.keys() == []
    return ds

def test_subclass():
    descs = {'ANotherClass': ANotherClass}
    ds = DocStorage().from_dict(descs)
    t = Tracer(ds)
    t.start_tracing()
    s = ANotherClass('blah blah')
    s.another_exposed_method(1)
    t.end_tracing()
    desc = ds.descs['ANotherClass']
    assert len(desc.fields) == 4
    inputcells = desc.fields['__init__'].inputcells
    assert len(inputcells) == 2
    inputcells = desc.fields['another_exposed_method'].inputcells
    assert len(inputcells) == 2
    bases = desc.bases
    assert len(bases) == 2
    return ds
    
def test_bases():
    class A:
        pass
    
    class B:
        pass
    
    class C(A,B):
        pass
    
    ds = DocStorage().from_dict({'C':C, 'B':B})
    dsa = DocStorageAccessor(ds)
    for desc in dsa.get_possible_base_classes('C'):
        assert desc is ds.descs['B'] or desc.is_degenerated
    return ds

def test_desc_from_pyobj():
    class A:
        pass

    class B(A):
        pass

    ds = DocStorage().from_dict({'A': A, 'B': B})
    dsa = DocStorageAccessor(ds)
    assert dsa.desc_from_pyobj(A, 'A') is ds.descs['A']
    return ds

def test_method_origin():
    class A:
        def foo(self):
            pass

    class B(A):
        def bar(self):
            pass

    class C(B):
        pass

    ds = DocStorage().from_dict({'C': C, 'B': B})
    dsa = DocStorageAccessor(ds)
    origin = dsa.get_method_origin('C.bar')
    assert origin is ds.descs['B']
    return ds

def test_multiple_methods():
    class A(object):
        def meth(self):
            pass
    
    class B(A):
        pass
    
    class C(A):
        pass
    
    ds = DocStorage().from_dict({'C':C, 'B':B})
    dsa = DocStorageAccessor(ds)
    t = Tracer(ds)
    t.start_tracing()
    B().meth()
    C().meth()
    t.end_tracing()
    assert len(ds.descs['B'].fields['meth'].call_sites) == 1
    assert len(ds.descs['C'].fields['meth'].call_sites) == 1
    return ds

def test_is_private():
    # XXX implicit test, but so are the rest :|
    class Foo(object):
        def foo(self):
            pass
        def _foo(self):
            pass
        def __foo(self):
            pass
        def trigger__foo(self):
            self.__foo()
        def __foo__(self):
            pass

    ds = DocStorage().from_dict({'Foo': Foo})
    dsa = DocStorageAccessor(ds)
    t = Tracer(ds)
    t.start_tracing()
    f = Foo()
    f.foo()
    f._foo()
    f.trigger__foo()
    f.__foo__()
    t.end_tracing()
    assert sorted(ds.descs['Foo'].getfields()) == ['__foo__', 'foo',
                                                     'trigger__foo']

def setup_fs_project():
    temp = py.test.ensuretemp('test_get_initpkg_star_items')
    temp.ensure("pkg/func.py").write(py.code.Source("""\
        def func(arg1):
            "docstring"
    """))
    temp.ensure('pkg/someclass.py').write(py.code.Source("""\
        class SomeClass(object):
            " docstring someclass "
            def __init__(self, somevar):
                self.somevar = somevar
                
            def get_somevar(self):
                " get_somevar docstring "
                return self.somevar
        SomeInstance = SomeClass(10)
    """))
    temp.ensure('pkg/somesubclass.py').write(py.code.Source("""\
        from someclass import SomeClass
        class SomeSubClass(SomeClass):
            " docstring somesubclass "
            #def get_somevar(self):
            #    return self.somevar + 1
    """))
    temp.ensure('pkg/somenamespace.py').write(py.code.Source("""\
        from pkg.main.sub import func
        import py
    
        def foo():
            return 'bar'

        def baz(qux):
            return qux

        quux = py.code.Source('print "foo"')
    """))
    temp.ensure("pkg/__init__.py").write(py.code.Source("""\
        from py.initpkg import initpkg
        initpkg(__name__, exportdefs = {
            'main.sub.func': ("./func.py", "func"),
            'main.SomeClass': ('./someclass.py', 'SomeClass'),
            #'main.SomeInstance': ('./someclass.py', 'SomeInstance'),
            'main.SomeSubClass': ('./somesubclass.py', 'SomeSubClass'),
            'other':             ('./somenamespace.py', '*'),
        })
    """))
    return temp, 'pkg'

def setup_pkg_docstorage():
    pkgdir, pkgname = setup_fs_project()
    py.std.sys.path.insert(0, str(pkgdir))
    # XXX test_get_initpkg_star_items depends on package not
    #     being imported already
    for key in py.std.sys.modules.keys():
        if key == pkgname or key.startswith(pkgname + "."):
            del py.std.sys.modules[key]
    pkg = __import__(pkgname)
    ds = DocStorage().from_pkg(pkg)
    return pkg, ds

def test_get_initpkg_star_items():
    pkg, ds = setup_pkg_docstorage()
    sit = get_star_import_tree(pkg.other, 'pkg.other')
    assert sorted(sit.keys()) == ['pkg.other.baz', 'pkg.other.foo']
    t = Tracer(ds)
    t.start_tracing()
    pkg.main.sub.func("a1")
    pkg.main.SomeClass(3).get_somevar()
    pkg.main.SomeSubClass(4).get_somevar()
    t.end_tracing()
    assert isinstance(ds.descs['main.sub.func'].inputcells[0], model.SomeString)
    desc = ds.descs['main.SomeClass']
    assert ds.descs['main.SomeClass.get_somevar'] is desc.fields['get_somevar']
    cell = desc.fields['get_somevar'].inputcells[0]
    assert isinstance(cell, model.SomeInstance)
    assert cell.classdef.cls is desc.pyobj
    desc = ds.descs['main.SomeSubClass']
    assert ds.descs['main.SomeSubClass.get_somevar'] is desc.fields['get_somevar']
    cell = desc.fields['get_somevar'].inputcells[0]
    assert isinstance(cell, model.SomeInstance)
    assert cell.classdef.cls is desc.pyobj

def test_pkg_to_dict():
    pkg, ds = setup_pkg_docstorage()
    assert sorted(pkg_to_dict(pkg).keys()) == ['main.SomeClass',
                                               'main.SomeSubClass',
                                               'main.sub.func',
                                               'other.baz',
                                               'other.foo']

