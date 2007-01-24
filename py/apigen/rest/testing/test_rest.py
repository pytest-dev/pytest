
""" tests document generation
"""

import py
from StringIO import StringIO

from py.__.apigen.rest.genrest import ViewVC, RestGen, PipeWriter, \
                                            DirWriter, FileWriter, \
                                            DirectPaste, DirectFS, \
                                            HTMLDirWriter, SourceView
from py.__.apigen.tracer.tracer import Tracer
from py.__.apigen.tracer.docstorage import DocStorage, DocStorageAccessor
from py.__.apigen.tracer.permastore import PermaDocStorage
import pickle

from py.__.apigen.tracer.testing.runtest import cut_pyc
from py.__.doc.conftest import genlinkchecks
from py.__.rest.rst import Rest, Paragraph
from py.__.rest.transform import HTMLHandler
# XXX: UUuuuuuuuuuuuuuuuuuuuuuuu, dangerous import

sorted = py.builtin.sorted

def _nl(s):
    """normalize newlines (converting to \n)"""
    s = s.replace('\r\n', '\n')
    s = s.replace('\r', '\n')
    return s

def setup_module(mod):
    mod.temppath = py.test.ensuretemp('restgen')

def fun_():
    pass

class SomeClass(object):
    """Some class definition"""
    
    def __init__(self, a):
        self.a = a
    
    def method(self, a, b, c):
        """method docstring"""
        return a + b + c
    
class SomeSubClass(SomeClass):
    """Some subclass definition"""

def fun(a, b, c):
    """Some docstring
    
        Let's make it span a couple of lines to be interesting...

        Note:

         * rest
         * should
         * be
         * supported
         * or
         * ignored...
    """
    return "d"

def test_direct_link():
    fname = cut_pyc(__file__)
    title, link = DirectPaste().getlink(fname, 2, "")
    assert title == '%s:%s' % (fname, 2)
    assert link == ''

def test_viewvc_link():
    vcview = ViewVC("http://codespeak.net/viewvc/")
    fname = cut_pyc(__file__)
    title, link = vcview.getlink(fname, 0, "")
    assert title == '%s:%s' % (fname, 0)
    assert link == ('http://codespeak.net/viewvc/py/apigen/rest/'
                        'testing/test_rest.py?view=markup')

def test_fs_link():
    title, link = DirectFS().getlink('/foo/bar/baz.py', 100, "func")
    assert title == '/foo/bar/baz.py:100'
    assert link == 'file:///foo/bar/baz.py'

class WriterTest(object):
    def get_filled_writer(self, writerclass, *args, **kwargs):
        dw = writerclass(*args, **kwargs)
        dw.write_section('foo', Rest(Paragraph('foo data')))
        dw.write_section('bar', Rest(Paragraph('bar data')))
        return dw

class TestDirWriter(WriterTest):
    def test_write_section(self):
        tempdir = temppath.ensure('dirwriter', dir=True)
        dw = self.get_filled_writer(DirWriter, tempdir)
        fpaths = tempdir.listdir('*.txt')
        assert len(fpaths) == 2
        assert sorted([f.basename for f in fpaths]) == ['bar.txt', 'foo.txt']
        assert _nl(tempdir.join('foo.txt').read()) == 'foo data\n'
        assert _nl(tempdir.join('bar.txt').read()) == 'bar data\n'
    
    def test_getlink(self):
        dw = DirWriter(temppath.join('dirwriter_getlink'))
        link = dw.getlink('function', 'Foo.bar', 'method_foo_bar')
        assert link == 'method_foo_bar.html'

class TestFileWriter(WriterTest):
    def test_write_section(self):
        tempfile = temppath.ensure('filewriter', file=True)
        fw = self.get_filled_writer(FileWriter, tempfile)
        data = tempfile.read()
        assert len(data)
    
    def test_getlink(self):
        fw = FileWriter(temppath.join('filewriter_getlink'))
        link = fw.getlink('function', 'Foo.bar', 'method_foo_bar')
        assert link == '#function-foo-bar'
        # only produce the same link target once...
        link = fw.getlink('function', 'Foo.bar', 'method_foo_bar')
        assert link is None
        link = fw.getlink('function', 'Foo.__init__', 'method_foo___init__')
        assert link == '#function-foo-init'

class TestPipeWriter(WriterTest):
    def test_write_section(self):
        s = StringIO()
        pw = self.get_filled_writer(PipeWriter, s)
        data = s.getvalue()
        assert len(data)

    def test_getlink(self):
        pw = PipeWriter(StringIO())
        link = pw.getlink('function', 'Foo.bar', 'method_foo_bar')
        assert link == 'method_foo_bar.txt'

class TestHTMLDirWriter(WriterTest):
    def test_write_section(self):
        tempdir = temppath.ensure('htmldirwriter', dir=1)
        hdw = self.get_filled_writer(HTMLDirWriter, HTMLHandler, HTMLHandler,
                                     tempdir)
        assert tempdir.join('foo.html').check(file=1)
        assert tempdir.join('bar.html').check(file=1)
        assert tempdir.join('foo.html').read().startswith('<html>')

class TestRest(object):
    def get_filled_docstorage(self):
        descs = {'SomeClass': SomeClass,
                 'SomeSubClass': SomeSubClass,
                 'fun':fun}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        s1 = SomeClass("a")
        fun(1, 2, s1)
        s2 = SomeSubClass("b")
        s2.method(1,2,3)
        fun(1, 3, s2)
        t.end_tracing()
        return DocStorageAccessor(ds)

    def get_filled_docstorage_modules(self):
        import somemodule
        import someothermodule
        descs = {
            'somemodule.SomeClass': somemodule.SomeClass,
            'someothermodule.SomeSubClass': someothermodule.SomeSubClass,
            'someothermodule.fun': someothermodule.fun,
        }
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        s1 = somemodule.SomeClass("a")
        someothermodule.fun(1, 2, s1)
        s2 = someothermodule.SomeSubClass("b")
        s2.method(1, 2, 3)
        someothermodule.fun(1, 3, s2)
        t.end_tracing()
        return DocStorageAccessor(ds)
    
    def check_rest(self, tempdir):
        from py.__.misc import rest
        for path in tempdir.listdir('*.txt'):
            try:
                rest.process(path)
            except ImportError:
                py.test.skip('skipping rest generation because docutils is '
                             'not installed (this is a partial skip, the rest '
                             'of the test was successful)')
        for path in tempdir.listdir('*.txt'):
            for item, arg1, arg2, arg3 in genlinkchecks(path):
                item(arg1, arg2, arg3)
    
    def test_generation_simple_api(self):
        ds = self.get_filled_docstorage()
        lg = DirectPaste()
        tempdir = temppath.ensure("simple_api", dir=True)
        r = RestGen(ds, lg, DirWriter(tempdir))
        r.write()
        basenames = [p.basename for p in tempdir.listdir('*.txt')]
        expected = [
            'class_SomeClass.txt',
            'class_SomeSubClass.txt',
            'function_fun.txt',
            'index.txt',
            'method_SomeClass.__init__.txt',
            'method_SomeClass.method.txt',
            'method_SomeSubClass.__init__.txt',
            'method_SomeSubClass.method.txt',
            'module_Unknown module.txt',
            'traceback_SomeClass.__init__.0.txt',
            'traceback_SomeSubClass.__init__.0.txt',
            'traceback_SomeSubClass.method.0.txt',
            'traceback_fun.0.txt',
            'traceback_fun.1.txt',
        ]
        print sorted(basenames)
        assert sorted(basenames) == expected
        # now we check out...
        self.check_rest(tempdir)
        tempdir = temppath.ensure("simple_api_ps", dir=True)
        if 0:
            ps = PermaDocStorage(ds)
            r = RestGen(ps, lg, DirWriter(tempdir))
            r.write()
            basenames = [p.basename for p in tempdir.listdir('*.txt')]
            assert sorted(basenames) == expected
            self.check_rest(tempdir)
            pickle.dumps(ps)

    def test_generation_modules(self):
        ds = self.get_filled_docstorage_modules()
        lg = DirectPaste()
        tempdir = temppath.ensure('module_api', dir=True)
        r = RestGen(ds, lg, DirWriter(tempdir))
        r.write()
        basenames = [p.basename for p in tempdir.listdir('*.txt')]
        expected = [
            'class_somemodule.SomeClass.txt',
            'class_someothermodule.SomeSubClass.txt',
            'function_someothermodule.fun.txt',
            'index.txt',
            'method_somemodule.SomeClass.__init__.txt',
            'method_somemodule.SomeClass.method.txt',
            'method_someothermodule.SomeSubClass.__init__.txt',
            'method_someothermodule.SomeSubClass.method.txt',
            'module_Unknown module.txt',
            'module_somemodule.txt',
            'module_someothermodule.txt',
            'traceback_somemodule.SomeClass.__init__.0.txt',
            'traceback_someothermodule.SomeSubClass.__init__.0.txt',
            'traceback_someothermodule.SomeSubClass.method.0.txt',
            'traceback_someothermodule.fun.0.txt',
            'traceback_someothermodule.fun.1.txt',
        ]
        print sorted(basenames)
        assert sorted(basenames) == expected

    def test_check_internal_links(self):
        ds = self.get_filled_docstorage()
        lg = DirectFS()
        tempdir = temppath.ensure('internal_links', dir=True)
        r = RestGen(ds, lg, DirWriter(tempdir))
        r.write()
        index = tempdir.join('module_Unknown module.txt')
        assert index.check(file=True)
        data = _nl(index.read())
        assert data.find('.. _`fun`: function_fun.html\n') > -1
        assert data.find('.. _`fun`: #function-fun\n') == -1

        tempfile = temppath.ensure('internal_links.txt',
                                  file=True)
        r = RestGen(ds, lg, FileWriter(tempfile))
        r.write()
        data = _nl(tempfile.read())
        assert data.find('.. _`fun`: #function-fun\n') > -1
        assert data.find('.. _`fun`: function_fun.html') == -1
        tempfile = temppath.ensure("internal_links_ps.txt", file=True)
        if 0:
            ps = PermaDocStorage(ds)
            r = RestGen(ps, lg, FileWriter(tempfile))
            r.write()
            data = _nl(tempfile.read())
            assert data.find('.. _`fun`: #function-fun\n') > -1
            assert data.find('.. _`fun`: function_fun.html') == -1
            pickle.dumps(ps)

    def test_check_section_order(self):
        # we use the previous method's data
        tempfile = temppath.join('internal_links.txt')
        if not tempfile.check():
            py.test.skip('depends on previous test, which failed')
        data = _nl(tempfile.read())
        # index should be above the rest
        assert data.find('classes\\:') > -1
        assert data.find('classes\\:') < data.find('function\\: fun')
        assert data.find('classes\\:') < data.find(
                                                    'class\\: SomeClass')
        # function definitions should be above class ones
        assert data.find('function\\: fun') > data.find('class\\: SomeClass')
        # class method definitions should be below the class defs
        assert data.find('class\\: SomeClass') < data.find(
                                            'method\\: SomeClass.method')
        # __init__ should be above other methods
        assert data.find('method\\: SomeClass.\\_\\_init\\_\\_') > -1
        assert data.find('method\\: SomeClass.\\_\\_init\\_\\_') < data.find(
                                                'method\\: SomeClass.method')
        # base class info
        assert py.std.re.search(r'class\\\: SomeSubClass.*'
                                r'base classes\\\:\n\^+[\n ]+\* `SomeClass`_.*'
                                r'`SomeSubClass.__init__',
                                data, py.std.re.S)

    def test_som_fun(self):
        descs = {'fun_': fun_}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        fun_()
        t.end_tracing()
        lg = DirectPaste()
        tempdir = temppath.ensure("some_fun", dir=True)
        r = RestGen(DocStorageAccessor(ds), lg, DirWriter(tempdir))
        r.write()
        self.check_rest(tempdir)

    def test_function_source(self):
        def blah():
            a = 3
            b = 4
            return a + b
        
        descs = {'blah': blah}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        blah()
        t.end_tracing()
        lg = DirectPaste()
        tempdir = temppath.ensure("function_source", dir=True)
        r = RestGen(DocStorageAccessor(ds), lg, DirWriter(tempdir))
        r.write()
        assert tempdir.join("function_blah.txt").read().find("a = 3") != -1
        self.check_rest(tempdir)
        ps = DocStorageAccessor(ds)
        r = RestGen(ps, lg, DirWriter(tempdir))
        r.write()
        assert tempdir.join("function_blah.txt").read().find("a = 3") != -1

    def test_function_arguments(self):
        def blah(a, b, c):
            return "axx"
        
        class C:
            pass
        
        descs = {'blah':blah}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        blah(3, "x", C())
        t.end_tracing()
        lg = DirectPaste()
        tempdir = temppath.ensure("function_args", dir=True)
        r = RestGen(DocStorageAccessor(ds), lg, DirWriter(tempdir))
        r.write()
        source = tempdir.join("function_blah.txt").read()
        call_point = source.find("call sites\:")
        assert call_point != -1
        assert source.find("a \:\: <Int>") < call_point
        assert source.find("b \:\: <String>") < call_point
        assert source.find("c \:\: <Instance of Class C>") < call_point
        self.check_rest(tempdir)

    def test_class_typedefs(self):
        class A(object):
            def __init__(self, x):
                pass

            def a(self):
                pass
        
        class B(A):
            def __init__(self, y):
                pass
        
        def xxx(x):
            return x
        
        descs = {'A': A, 'B': B, 'xxx':xxx}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        xxx(A(3))
        xxx(B("f"))
        t.end_tracing()
        lg = DirectPaste()
        tempdir = temppath.ensure("classargs", dir=True)
        r = RestGen(DocStorageAccessor(ds), lg, DirWriter(tempdir))
        r.write()
        source = tempdir.join("function_xxx.txt").read()
        call_point = source.find("call sites\:")
        assert call_point != -1
        print source
        assert -1 < source.find("x \:\: <Instance of AnyOf( `Class B`_ , "
                                "`Class A`_ )>") < call_point
        source = tempdir.join('method_B.a.txt').read()
        py.test.skip('XXX needs to be fixed, clueless atm though')
        assert source.find('**origin** \: `A`_') > -1
        self.check_rest(tempdir)

    def test_exc_raising(self):
        def x():
            try:
                1/0
            except:
                pass
        
        descs = {'x':x}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        x()
        t.end_tracing()
        lg = DirectPaste()
        tempdir = temppath.ensure("exc_raising", dir=True)
        r = RestGen(DocStorageAccessor(ds), lg, DirWriter(tempdir))
        r.write()
        source = tempdir.join('function_x.txt').open().read()
        assert source.find('ZeroDivisionError') < source.find('call sites\:')


    def test_nonexist_origin(self):
        class A:
            def method(self):
                pass
        
        class B(A):
            pass
        
        descs = {'B':B}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        B().method()
        t.end_tracing()
        lg = DirectPaste()
        tempdir = temppath.ensure("nonexit_origin", dir=True)
        r = RestGen(DocStorageAccessor(ds), lg, DirWriter(tempdir))
        r.write()
        self.check_rest(tempdir)

    def test_sourceview(self):
        class A:
            def method(self):
                pass
        
        descs = {'A':A}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        A().method()
        t.end_tracing()
        lg = SourceView('http://localhost:8000')
        tempdir = temppath.ensure("sourceview", dir=True)
        r = RestGen(DocStorageAccessor(ds), lg, DirWriter(tempdir))
        r.write()
        self.check_rest(tempdir)
        assert tempdir.join('traceback_A.method.0.txt').open().read().find(
           '.. _`/py/apigen/rest/testing/test\_rest.py\:A.method`: http://localhost:8000/py/apigen/rest/testing/test_rest.py#A.method') != -1

    def test_sourceview_fun(self):
        def f():
            pass

        descs = {'f':f}
        ds = DocStorage().from_dict(descs)
        t = Tracer(ds)
        t.start_tracing()
        f()
        t.end_tracing()
        tempdir = temppath.ensure("sourceview_fun", dir=True)
        lg = SourceView('http://localhost:8000')
        r = RestGen(DocStorageAccessor(ds), lg, DirWriter(tempdir))
        r.write()
        self.check_rest(tempdir)
        assert tempdir.join('function_f.txt').open().read().find(
            '.. _`/py/apigen/rest/testing/test\_rest.py\:f`: http://localhost:8000/py/apigen/rest/testing/test_rest.py#f') != -1
