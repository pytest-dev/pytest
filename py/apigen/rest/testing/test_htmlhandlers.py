import py
from py.__.apigen.rest.htmlhandlers import PageHandler

def test_breadcrumb():
    h = PageHandler()
    for fname, expected in [
            ('module_py', '<a href="module_py.html">py</a>'),
            ('module_py.test',
                '<a href="module_py.test.html">py.test</a>'),
            ('class_py.test',
                ('<a href="module_py.html">py</a>.'
                 '<a href="class_py.test.html">test</a>')),
            ('class_py.test.foo',
                ('<a href="module_py.test.html">py.test</a>.'
                 '<a href="class_py.test.foo.html">foo</a>')),
            ('class_py.test.foo.bar',
                ('<a href="module_py.test.foo.html">py.test.foo</a>.'
                 '<a href="class_py.test.foo.bar.html">bar</a>')),
            ('function_foo', '<a href="function_foo.html">foo</a>'),
            ('function_foo.bar',
                ('<a href="module_foo.html">foo</a>.'
                 '<a href="function_foo.bar.html">bar</a>')),
            ('function_foo.bar.baz',
                ('<a href="module_foo.bar.html">foo.bar</a>.'
                 '<a href="function_foo.bar.baz.html">baz</a>')),
            ('method_foo.bar',
                ('<a href="class_foo.html">foo</a>.'
                 '<a href="method_foo.bar.html">bar</a>')),
            ('method_foo.bar.baz',
                ('<a href="module_foo.html">foo</a>.'
                 '<a href="class_foo.bar.html">bar</a>.'
                 '<a href="method_foo.bar.baz.html">baz</a>')),
            ('method_foo.bar.baz.qux',
                ('<a href="module_foo.bar.html">foo.bar</a>.'
                 '<a href="class_foo.bar.baz.html">baz</a>.'
                 '<a href="method_foo.bar.baz.qux.html">qux</a>')),
            ]:
        html = ''.join([unicode(el) for el in h.breadcrumb(fname)])
        print fname
        print html
        assert html == expected
