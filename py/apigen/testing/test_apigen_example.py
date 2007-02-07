# -*- coding: UTF-8 -*-
import py
html = py.xml.html
from py.__.apigen.linker import TempLinker
from py.__.apigen.htmlgen import *
from py.__.apigen.tracer.docstorage import DocStorage, DocStorageAccessor
from py.__.apigen.tracer.tracer import Tracer
from py.__.apigen.project import Project
from py.__.test.web import webcheck
from py.__.apigen.conftest import option

def run_string_sequence_test(data, seq):
    currpos = -1
    for s in seq:
        newpos = data.find(s)
        if currpos >= newpos:
            if newpos == -1:
                message = 'not found'
            else:
                message = 'unexpected position: %s' % (newpos,)
            py.test.fail('string %r: %s' % (s, message))
        currpos = newpos

def setup_fs_project():
    temp = py.test.ensuretemp('apigen_example')
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
            def get_somevar(self):
                return self.somevar + 1
    """))
    temp.ensure('pkg/somenamespace.py').write(py.code.Source("""\
        def foo():
            return 'bar'
        def baz(qux):
            return qux
    """))
    temp.ensure("pkg/__init__.py").write(py.code.Source("""\
        from py.initpkg import initpkg
        initpkg(__name__, exportdefs = {
            'main.sub.func': ("./func.py", "func"),
            'main.SomeClass': ('./someclass.py', 'SomeClass'),
            'main.SomeInstance': ('./someclass.py', 'SomeInstance'),
            'main.SomeSubClass': ('./somesubclass.py', 'SomeSubClass'),
            'main.SomeSubClass': ('./somesubclass.py', 'SomeSubClass'),
            'other':             ('./somenamespace.py', '*'),
            '_test':             ('./somenamespace.py', '*'),
        })
    """))
    return temp, 'pkg'

def get_dsa(fsroot, pkgname):
    py.std.sys.path.insert(0, str(fsroot))
    pkg = __import__(pkgname)
    ds = DocStorage()
    ds.from_pkg(pkg)
    dsa = DocStorageAccessor(ds)
    return ds, dsa

def _checkhtml(htmlstring):
    if isinstance(htmlstring, unicode):
        htmlstring = htmlstring.encode('UTF-8', 'replace')
    assert isinstance(htmlstring, str)
    if option.webcheck:
        webcheck.check_html(htmlstring)
    else:
        py.test.skip("pass --webcheck to validate html produced in tests "
                     "(partial skip: the test has succeeded up until here)")

def _checkhtmlsnippet(htmlstring):
    # XXX wrap page around snippet and validate 
    pass
    #newstring = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    #"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n""" + unicode(h)
    #_checkhtml(newstring)

class AbstractBuilderTest(object):
    def setup_class(cls):
        cls.fs_root, cls.pkg_name = setup_fs_project()
        cls.ds, cls.dsa = get_dsa(cls.fs_root, cls.pkg_name)
        cls.project = Project()

    def setup_method(self, meth):
        self.base = base = py.test.ensuretemp('%s_%s' % (
                            self.__class__.__name__, meth.im_func.func_name))
        self.linker = linker = TempLinker()
        namespace_tree = create_namespace_tree(['main.sub',
                                                'main.sub.func',
                                                'main.SomeClass',
                                                'main.SomeSubClass',
                                                'main.SomeInstance',
                                                'other.foo',
                                                'other.bar',
                                                '_test'])
        self.namespace_tree = namespace_tree
        self.apb = ApiPageBuilder(base, linker, self.dsa,
                                  self.fs_root.join(self.pkg_name),
                                  namespace_tree, self.project)
        self.spb = SourcePageBuilder(base, linker,
                                     self.fs_root.join(self.pkg_name),
                                     self.project)

class TestApiPageBuilder(AbstractBuilderTest):
    def test_build_callable_view(self):
        ds, dsa = get_dsa(self.fs_root, self.pkg_name)
        t = Tracer(ds)
        t.start_tracing()
        pkg = __import__(self.pkg_name)
        pkg.main.sub.func(10)
        pkg.main.sub.func(pkg.main.SomeClass(10))
        t.end_tracing()
        apb = ApiPageBuilder(self.base, self.linker, dsa, self.fs_root,
                             self.namespace_tree, 'root docstring')
        snippet = apb.build_callable_view('main.sub.func')
        html = snippet.unicode()
        print html
        # XXX somewhat grokky tests because the order of the items may change
        assert 'arg1: AnyOf(' in html
        pos1 = html.find('arg1: AnyOf(')
        assert pos1 > -1
        pos2 = html.find('href="', pos1)
        assert pos2 > pos1
        pos3 = html.find('Class SomeClass', pos2)
        assert pos3 > pos2
        pos4 = html.find('Int&gt;', pos1)
        assert pos4 > pos1
        pos5 = html.find('return value:', pos4)
        assert pos5 > pos4 and pos5 > pos3
        pos6 = html.find('&lt;None&gt;', pos5)
        assert pos6 > pos5
        pos7 = html.find('source: %s' % (self.fs_root.join('pkg/func.py'),),
                          pos6)
        assert pos7 > pos6
        pos8 = html.find('def func(arg1):', pos7)
        assert pos8 > pos7
        _checkhtmlsnippet(html)

    def test_build_function_pages(self):
        self.apb.build_function_pages(['main.sub.func'])
        funcfile = self.base.join('api/main.sub.func.html')
        assert funcfile.check()
        html = funcfile.read()
        _checkhtml(html)

    def test_build_class_view(self):
        snippet = self.apb.build_class_view('main.SomeClass')
        html = snippet.unicode()
        _checkhtmlsnippet(html)

    def test_build_class_pages(self):
        self.apb.build_class_pages(['main.SomeClass', 'main.SomeSubClass'])
        clsfile = self.base.join('api/main.SomeClass.html')
        assert clsfile.check()
        html = clsfile.read()
        _checkhtml(html)

    def test_build_class_pages_instance(self):
        self.apb.build_class_pages(['main.SomeClass',
                                    'main.SomeSubClass',
                                    'main.SomeInstance'])
        clsfile = self.base.join('api/main.SomeInstance.html')
        assert clsfile.check()
        html = clsfile.read()
        print html
        run_string_sequence_test(html, [
            'instance of SomeClass()',
        ])

    def test_build_class_pages_nav_links(self):
        self.apb.build_class_pages(['main.SomeSubClass',
                                    'main.SomeClass'])
        self.apb.build_namespace_pages()
        # fake some stuff that would be built from other methods
        self.linker.replace_dirpath(self.base, False)
        clsfile = self.base.join('api/main.SomeClass.html')
        assert clsfile.check()
        html = clsfile.read()
        print html
        run_string_sequence_test(html, [
            'href="../style.css"',
            'href="../apigen_style.css"',
            'src="../api.js"',
            'href="index.html">pkg',
            'href="main.html">main',
            'href="main.SomeClass.html">SomeClass',
            'href="main.SomeSubClass.html">SomeSubClass',
        ])
        assert 'href="main.sub.func.html"' not in html
        assert 'href="_test' not in html
        assert 'href="main.sub.html">sub' in html
        _checkhtml(html)

    def test_build_class_pages_base_link(self):
        self.apb.build_class_pages(['main.SomeSubClass',
                                    'main.SomeClass'])
        self.linker.replace_dirpath(self.base, False)
        clsfile = self.base.join('api/main.SomeSubClass.html')
        assert clsfile.check()
        html = clsfile.read()
        print html
        run_string_sequence_test(html, [
            'href="../style.css"',
            'href="main.SomeClass.html">main.SomeClass',
        ])
        _checkhtml(html)

    def test_source_links(self):
        self.apb.build_class_pages(['main.SomeSubClass', 'main.SomeClass'])
        self.spb.build_pages(self.fs_root)
        self.linker.replace_dirpath(self.base, False)
        funchtml = self.base.join('api/main.SomeClass.html').read()
        assert funchtml.find('href="../source/pkg/someclass.py.html"') > -1
        _checkhtml(funchtml)

    def test_build_namespace_pages(self):
        self.apb.build_namespace_pages()
        mainfile = self.base.join('api/main.html')
        assert mainfile.check()
        html = mainfile.read()
        print html
        run_string_sequence_test(html, [
            'index of main namespace',
        ])
        otherfile = self.base.join('api/other.html')
        assert otherfile.check()
        otherhtml = otherfile.read()
        print otherhtml
        run_string_sequence_test(otherhtml, [
            'index of other namespace',
        ])
        _checkhtml(html)
        _checkhtml(otherhtml)

    def test_build_namespace_pages_index(self):
        self.apb.build_namespace_pages()
        pkgfile = self.base.join('api/index.html')
        assert pkgfile.check()
        html = pkgfile.read()
        assert 'index of project pkg namespace'
        _checkhtml(html)

    def test_build_namespace_pages_subnamespace(self):
        self.apb.build_namespace_pages()
        subfile = self.base.join('api/main.sub.html')
        assert subfile.check()
        html = subfile.read()
        _checkhtml(html)

    def test_build_function_api_pages_nav(self):
        self.linker.set_link('main.sub', 'api/main.sub.html')
        self.linker.set_link('', 'api/index.html')
        self.linker.set_link('main', 'api/main.html')
        self.apb.build_function_pages(['main.sub.func'])
        self.linker.replace_dirpath(self.base, False)
        funcfile = self.base.join('api/main.sub.func.html')
        html = funcfile.read()
        print html
        run_string_sequence_test(html, [
            '<a href="index.html">',
            '<a href="main.html">',
            '<a href="main.sub.html">',
            '<a href="main.sub.func.html">',
        ])
        _checkhtml(html)

    def test_build_function_navigation(self):
        self.apb.build_namespace_pages()
        self.apb.build_function_pages(['main.sub.func'])
        self.apb.build_class_pages(['main.SomeClass',
                                    'main.SomeSubClass',
                                    'main.SomeInstance'])
        self.linker.replace_dirpath(self.base, False)
        html = self.base.join('api/main.sub.func.html').read()
        print html
        # XXX NOTE: do not mess with the string below, the spaces between the
        # <div> and <a> are actually UTF-8 \xa0 characters (non-breaking
        # spaces)!
        assert """\
    <div class="sidebar">
      <div class="selected"><a href="index.html">pkg</a></div>
      <div class="selected">  <a href="main.html">main</a></div>
      <div>    <a href="main.SomeClass.html">SomeClass</a></div>
      <div>    <a href="main.SomeInstance.html">SomeInstance</a></div>
      <div>    <a href="main.SomeSubClass.html">SomeSubClass</a></div>
      <div class="selected">    <a href="main.sub.html">sub</a></div>
      <div class="selected">      <a href="main.sub.func.html">func</a></div>
      <div>  <a href="other.html">other</a></div></div>
""" in html

    def test_build_root_namespace_view(self):
        self.apb.build_namespace_pages()
        self.linker.replace_dirpath(self.base, False)
        rootfile = self.base.join('api/index.html')
        assert rootfile.check()
        html = rootfile.read()
        assert '<a href="main.html">' in html
        _checkhtml(html)

class TestSourcePageBuilder(AbstractBuilderTest):
    def test_build_pages(self):
        self.spb.build_pages(self.fs_root)
        somesource = self.base.join('source/pkg/func.py.html').read()
        _checkhtml(somesource)

    def test_build_pages_nav(self):
        self.spb.build_pages(self.fs_root)
        self.linker.replace_dirpath(self.base, False)
        funcsource = self.base.join('source/pkg/func.py.html')
        assert funcsource.check(file=True)
        html = funcsource.read()
        print html
        run_string_sequence_test(html, [
            'href="../../style.css"',
            '<a href="index.html">pkg</a>',
            '<a href="someclass.py.html">someclass.py</a>',
            '<a href="somesubclass.py.html">somesubclass.py</a>',
        ])

    def test_build_dir_page(self):
        self.spb.build_pages(self.fs_root)
        self.linker.replace_dirpath(self.base, False)
        pkgindex = self.base.join('source/pkg/index.html')
        assert pkgindex.check(file=True)
        html = pkgindex.read()
        print html
        run_string_sequence_test(html, [
            'href="../../style.css"',
            '<a href="index.html">pkg</a>',
            '<a href="func.py.html">func.py</a>',
            '<a href="someclass.py.html">someclass.py</a>',
            '<a href="somesubclass.py.html">somesubclass.py</a>',
            '<h2>directories</h2>',
            '<h2>files</h2>'])
        _checkhtml(html)

    def test_build_source_page(self):
        self.spb.build_pages(self.fs_root)
        self.linker.replace_dirpath(self.base, False)
        funcsource = self.base.join('source/pkg/func.py.html')
        assert funcsource.check(file=True)
        html = funcsource.read()
        print html
        assert ('<span class="alt_keyword">def</span> func(arg1)') in html

    def test_build_navigation_root(self):
        self.spb.build_pages(self.fs_root)
        self.linker.replace_dirpath(self.base)
        html = self.base.join('source/pkg/index.html').read()
        print html
        run_string_sequence_test(html, [
            'href="index.html">pkg',
            'href="func.py.html">func.py',
            'href="someclass.py.html">someclass.py',
            'href="somesubclass.py.html">somesubclass.py',
        ])

