# -*- coding: UTF-8 -*-

""" test of html generation
"""

from py.__.apigen.source.html import prepare_line, create_html, HTMLDocument, \
                                     get_module_encoding
from py.__.apigen.source.browser import parse_path
from py.__.apigen.source.color import Tokenizer, PythonSchema
from py.xml import html

import py
import os

def create_html_and_show(path):
    mod = parse_path(path)
    html = create_html(mod)
    testfile = py.test.ensuretemp("htmloutput").ensure("test.html")
    testfile.write(unicode(html))
    return testfile

def test_basic():
    tmp = py.test.ensuretemp("sourcehtml")
    inp = tmp.ensure("one.py")
    inp.write(py.code.Source("""
    def func_one():
        pass
    
    def func_two(x, y):
        x = 1
        y = 2
        return x + y
    
    class B:
        pass
    
    class A(B):
        def meth1(self):
            pass
        
        def meth2(self):
            pass
    """))
    
    testfile = create_html_and_show(inp)
    data = testfile.open().read()
    assert data.find('<a href="#func_one"') != -1
    assert data.find('<a href="#func_two"') != -1
    assert data.find('<a href="#B"') != -1
    assert data.find('<a href="#A"') != -1
    assert data.find('<a href="#A.meth1"') != -1

class _HTMLDocument(HTMLDocument):
    def __init__(self):
        self.encoding = 'ascii'

class TestHTMLDocument(object):
    def test_head(self):
        doc = _HTMLDocument()
        head = doc.create_head()
        assert isinstance(head, html.head)
        rendered = unicode(head)
        assert rendered.find('<title>source view</title>') > -1
        assert py.std.re.search('<style type="text/css">[^<]+</style>',
                                rendered)

    def test_body(self):
        doc = _HTMLDocument()
        body = doc.create_body()
        assert unicode(body) == '<body></body>'

    def test_table(self):
        doc = _HTMLDocument()
        table, tbody = doc.create_table()
        assert isinstance(table, html.table)
        assert isinstance(tbody, html.tbody)
        assert tbody == table[0]

    def test_add_row(self):
        doc = HTMLDocument('ascii')
        doc.add_row(1, ['""" this is a foo implementation """'])
        doc.add_row(2, [''])
        doc.add_row(3, ['class ', html.a('Foo', name='Foo'), ':'])
        doc.add_row(4, ['    pass'])
        tbody = doc.tbody
        assert len(tbody) == 4
        assert unicode(tbody[0][0]) == '<td class="lineno">1</td>'
        assert unicode(tbody[0][1]) == ('<td class="code">'
                                        '<span class="string">'
                                        '&quot;&quot;&quot; '
                                        'this is a foo implementation '
                                        '&quot;&quot;&quot;'
                                        '</span></td>')
        assert unicode(tbody[1][1]) == '<td class="code">&#xa0;</td>'
        assert unicode(tbody[2][1]) == ('<td class="code">'
                                        '<span class="alt_keyword">class'
                                        '</span> '
                                        '<a name="Foo">Foo</a>:</td>')
        assert unicode(tbody[3][1]) == ('<td class="code">    '
                                        '<span class="alt_keyword">pass'
                                        '</span></td>')

    def test_unicode(self):
        doc = HTMLDocument('ascii')
        h = unicode(doc)
        print h
        assert py.std.re.match(r'<html>\s*<head>\s*<title>[^<]+</title>'
                                '.*</body>\w*</html>$', h, py.std.re.S)

def prepare_line_helper(line, tokenizer=None, encoding='ascii'):
    if tokenizer is None:
        tokenizer = Tokenizer(PythonSchema)
    l = prepare_line(line, tokenizer, encoding)
    return ''.join([unicode(i) for i in l])

def test_prepare_line_basic():
    result = prepare_line_helper(['see if this works'])
    assert result == 'see <span class="keyword">if</span> this works'
    result = prepare_line_helper(['see if this ',
                                html.a('works', name='works'),' too'])
    assert result == ('see <span class="keyword">if</span> this '
                      '<a name="works">works</a> too')
    result = prepare_line_helper(['see if something else works'])
    assert result == ('see <span class="keyword">if</span> something '
                      '<span class="keyword">else</span> works')
    result = prepare_line_helper(['see if something ',
                                html.a('else', name='else'), ' works too'])
    assert result == ('see <span class="keyword">if</span> something '
                      '<a name="else">else</a> works too')

def test_prepare_line_strings():
    result = prepare_line_helper(['foo = "bar"'])
    assert result == 'foo = <span class="string">&quot;bar&quot;</span>'

    result = prepare_line_helper(['"spam"'])
    assert result == '<span class="string">&quot;spam&quot;</span>'
    
def test_prepare_line_multiline_strings():
    # test multiline strings
    t = Tokenizer(PythonSchema)
    result = prepare_line_helper(['"""start of multiline'], t)
    assert result == ('<span class="string">&quot;&quot;&quot;start of '
                      'multiline</span>')
    result = prepare_line_helper(['see if it doesn\'t touch this'], t)
    assert result == ('<span class="string">see if it doesn&apos;t touch '
                      'this</span>')
    result = prepare_line_helper(['"""'], t)
    assert result == '<span class="string">&quot;&quot;&quot;</span>'
    result = prepare_line_helper(['see if it colours this again'], t)
    assert result == ('see <span class="keyword">if</span> it colours '
                      'this again')

def test_prepare_line_nonascii():
    result = prepare_line_helper(['"föö"'], encoding='UTF-8')
    assert (result ==
            unicode('<span class="string">&quot;föö&quot;</span>', 'UTF-8'))

def test_get_encoding_ascii():
    temp = py.test.ensuretemp('test_get_encoding')
    fpath = temp.join('ascii.py')
    fpath.write(str(py.code.Source("""\
        def foo():
            return 'foo'
    """)))
    # XXX I think the specs say we have to assume latin-1 here...
    assert get_module_encoding(fpath.strpath) == 'ISO-8859-1'

def test_get_encoding_for_real():
    temp = py.test.ensuretemp('test_get_encoding')
    fpath = temp.join('utf-8.py')
    fpath.write(str(py.code.Source("""\
        #!/usr/bin/env python
        # -*- coding: UTF-8 -*-

        def foo():
            return 'föö'
    """)))
    assert get_module_encoding(fpath.strpath) == 'UTF-8'

def test_get_encoding_matching_pattern_elsewhere():
    temp = py.test.ensuretemp('test_get_encoding')
    fpath = temp.join('matching_pattern.py')
    fpath.write(str(py.code.Source("""\
        #!/usr/bin/env python
        
        def foo(coding=None):
            pass
    """)))
    assert get_module_encoding(fpath.strpath) == 'ISO-8859-1'

