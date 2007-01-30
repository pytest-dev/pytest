import py
from py.__.rest.rst import *
from py.__.rest.transform import *

def convert_to_html(tree):
    handler = HTMLHandler()
    t = RestTransformer(tree)
    t.parse(handler)
    return handler.html

class HTMLHandler(py.__.rest.transform.HTMLHandler):
    def startDocument(self):
        pass
    endDocument = startDocument

def test_transform_basic_html():
    for rest, expected in ((Rest(Title('foo')), '<h1>foo</h1>'),
                           (Rest(Paragraph('foo')), '<p>foo</p>'),
                           (Rest(SubParagraph('foo')),
                            '<p class="sub">foo</p>'),
                           (Rest(LiteralBlock('foo\tbar')),
                            '<pre>foo\tbar</pre>'),
                           (Rest(Paragraph(Link('foo',
                                                'http://www.foo.com/'))),
                            '<p><a href="http://www.foo.com/">foo</a></p>')):
        html = convert_to_html(rest)
        assert html == expected

def test_transform_list_simple():
    rest = Rest(ListItem('foo'), ListItem('bar'))
    html = convert_to_html(rest)
    assert html == '<ul>\n  <li>foo</li>\n  <li>bar</li></ul>'

def test_transform_list_nested():
    rest = Rest(ListItem('foo'), ListItem('bar', ListItem('baz')))
    html = convert_to_html(rest)
    assert html == ('<ul>\n  <li>foo</li>\n  <li>bar\n    <ul>'
                    '\n      <li>baz</li></ul></li></ul>')

