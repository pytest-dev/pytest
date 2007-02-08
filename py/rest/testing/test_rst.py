
""" rst generation tests
"""

from py.__.rest.rst import *
from py.__.doc.conftest import restcheck
import traceback

tempdir = py.test.ensuretemp('rest')
def checkrest(rest):
    fname = traceback.extract_stack()[-2][2]
    i = 0
    while True:
        if i == 0:
            filename = '%s.txt' % (fname,)
        else:
            filename = '%s_%s.txt' % (fname, i)
        tempfile = tempdir.join(filename)
        if not tempfile.check():
            break
        i += 1
    tempfile.write(rest)
    restcheck(tempfile)
    return tempfile.new(ext='.html').read()

def test_escape_text():
    txt = Paragraph('*escape* ``test``').text()
    assert txt == '\\*escape\\* \\`\\`test\\`\\`'
    html = checkrest(txt)
    assert '*escape* ``test``' in html

def test_escape_markup_simple():
    txt = Paragraph(Em('*em*')).text()
    assert txt == '*\\*em\\**'
    html = checkrest(txt)
    assert '<em>*em*</em>' in html

def test_escape_underscore():
    txt = Rest(Paragraph('foo [1]_')).text()
    assert txt == "foo [1]\\_\n"
    html = checkrest(txt)
    assert 'foo [1]_' in html

def test_escape_markup_spaces_docutils_nastyness():
    txt = Rest(Paragraph(Em('foo *bar* baz'))).text()
    assert txt == '*foo \\*bar\\* baz*\n'
    html = checkrest(txt)
    assert '<em>foo *bar* baz</em>' in html

def test_escape_literal():
    txt = LiteralBlock('*escape* ``test``').text()
    assert txt == '::\n\n  *escape* ``test``'
    html = checkrest(txt)
    assert '>\n*escape* ``test``\n</pre>' in html

def test_escape_markup_obvious():
    txt = Em('foo*bar').text()
    assert txt == '*foo\\*bar*'
    html = checkrest(txt)
    assert '<em>foo*bar</em>' in html

def test_escape_markup_text_1():
    txt = Paragraph(Em('foo'), "*bar").text()
    assert txt == '*foo* \\*bar'
    html = checkrest(txt)
    assert '<em>foo</em> *bar' in html

def test_escape_markup_text_2():
    txt = Paragraph(Em('foo'), "bar*").text()
    assert txt == '*foo* bar\\*'
    html = checkrest(txt)
    assert '<em>foo</em> bar*' in html

def test_illegal_parent():
    Rest(Paragraph(Text('spam')))
    py.test.raises(RestError, 'Rest(Text("spam"))')
    py.test.raises(RestError, 'ListItem(Paragraph(Text("eggs")))')

def test_text_basic():
    txt = Text("dupa").text()
    assert txt == "dupa"

def test_basic_inline():
    txt = Em('foo').text()
    assert txt == '*foo*'

def test_basic_inline_2():
    txt = Strong('bar').text()
    assert txt == '**bar**'

def test_text_multiple_arguments():
    txt = Paragraph(Text("dupa"), Text("dupa")).text()
    assert txt == "dupa dupa"

def test_text_join():
    txt = Paragraph(Text("worse things"))
    txt = txt.join(Text("happen at sea"), Text("you know"))
    assert txt.text() == "worse things happen at sea you know"

def test_text_add():
    p = Paragraph(Text('grmbl'))
    p2 = p.add(Text('grmbl too'))
    assert p2.text() == 'grmbl too'
    assert p.text() == 'grmbl grmbl too'

def test_paragraph_basic():
    txt = Paragraph(Text('spam')).text()
    assert txt == 'spam'

def test_paragraph_string():
    txt = Paragraph("eggs").text()
    assert txt == "eggs"
    checkrest(txt)

def test_paragraph_join():
    txt = Rest(Paragraph(Text("a")), Paragraph(Text("b"))).text()
    assert txt == "a\n\nb\n"

def test_paragraph_indent():
    txt = Paragraph(Text("a"), indent=" ").text()
    assert txt == " a"
    checkrest(txt)
    txt = Paragraph(Text("  a "), indent=" ").text()
    assert txt == " a"

def test_paragraph_width():
    txt = Paragraph(Text("a b c d e f"), width=3, indent=" ").text()
    assert txt == ' a\n b\n c\n d\n e\n f'
    checkrest(txt)
    text = """
Lorem ipsum dolor sit amet, consectetuer
adipiscing elit. Vestibulum malesuada
eleifend leo. Sed faucibus commodo libero. 
Mauris elementum fringilla velit. Ut
sem urna, aliquet sed, molestie at, viverra 
id, justo. In ornare lacinia turpis. Etiam 
et ipsum. Quisque at lacus. Etiam 
pellentesque, enim porta pulvinar viverra, 
libero elit iaculis justo, vitae convallis 
pede purus vel arcu. Morbi aliquam lacus 
et urna. Donec commodo pellentesque mi.
"""
    expected = """\
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Vestibulum malesuada
eleifend leo. Sed faucibus commodo libero. Mauris elementum fringilla velit. Ut
sem urna, aliquet sed, molestie at, viverra id, justo. In ornare lacinia
turpis. Etiam et ipsum. Quisque at lacus. Etiam pellentesque, enim porta
pulvinar viverra, libero elit iaculis justo, vitae convallis pede purus vel
arcu. Morbi aliquam lacus et urna. Donec commodo pellentesque mi."""
    txt = Paragraph(text, width=80).text()
    print repr(txt)
    print repr(expected)
    assert txt == expected
    checkrest(txt)

def test_paragraph_stripping():
    txt = Paragraph(Text('\n foo bar\t')).text()
    assert txt == 'foo bar'
    checkrest(txt)

def test_blockquote():
    expected = """\
Text

::

  def fun():
   some

Paragraph
"""
    txt = Rest(Paragraph("Text"), LiteralBlock("def fun():\n some"), \
               Paragraph("Paragraph")).text()
    print repr(txt)
    assert txt == expected
    checkrest(txt)

def test_blockquote_empty():
    expected = """\
Foo

Bar
"""
    txt = Rest(Paragraph('Foo'), LiteralBlock(''), Paragraph('Bar')).text()
    print repr(txt)
    assert txt == expected
    checkrest(txt)

def test_title():
    txt = Title(Text("Some title"), belowchar="=").text()
    assert txt == "Some title\n=========="
    checkrest(txt)
    txt =  Title("Some title", belowchar="#", abovechar="#").text()
    assert txt == "##########\nSome title\n##########"
    html = checkrest(txt)
    assert '>Some title</h1>' in html

def test_title_long():
    txt = Title('Some very long title that doesn\'t fit on a single line '
                'but still should not be split into multiple lines').text()
    assert txt == ("Some very long title that doesn't fit on a single line "
                   "but still should not be split into multiple lines\n"
                   "======================================================="
                   "=================================================")
    checkrest(txt)

def test_title_long_with_markup():
    txt = Title('Some very long title with', Em('some markup'),
                'to test whether that works as expected too...').text()
    assert txt == ("Some very long title with *some markup* to test whether "
                   "that works as expected too...\n"
                   "========================================================"
                   "=============================")
    checkrest(txt)

def test_title_escaping():
    txt = Title('foo *bar* baz').text()
    assert txt == 'foo \\*bar\\* baz\n==============='
    checkrest(txt)

def test_link():
    expected = "`some link`_\n\n.. _`some link`: http://codespeak.net\n\n"
    txt = Rest(Paragraph(Link("some link", "http://codespeak.net"))).text()
    assert txt == expected
    html = checkrest(txt)
    assert ' href="http://codespeak.net">some link</a>' in html

def test_link_same_text_and_target():
    txt = Rest(Paragraph(Link('some link', 'bar'), 'foo',
                         Link('some link', 'bar'))
                         ).text()
    expected = '`some link`_ foo `some link`_\n\n.. _`some link`: bar\n\n'
    assert txt == expected

def test_link_same_text_different_target():
    py.test.raises(ValueError, ("Rest(Paragraph(Link('some link', 'foo'),"
                                  "Link('some link', 'bar'))).text()"))

def test_text_multiline():
    expected = """\
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Vestibulum malesuada
eleifend leo. Sed faucibus commodo libero. Mauris elementum fringilla velit. Ut
sem urna, aliquet sed, molestie at, viverra id, justo. In ornare lacinia
turpis. Etiam et ipsum. Quisque at lacus. Etiam pellentesque, enim porta
pulvinar viverra, libero elit iaculis justo, vitae convallis pede purus vel
arcu. Morbi aliquam lacus et urna. Donec commodo pellentesque mi.
"""
    txt = Rest(Paragraph('Lorem ipsum dolor sit amet, consectetuer adipiscing '
                         'elit. Vestibulum malesuada eleifend leo. Sed '
                         'faucibus commodo libero. Mauris elementum fringilla '
                         'velit. Ut sem urna, aliquet sed, molestie at, '
                         'viverra id, justo. In ornare lacinia turpis. Etiam '
                         'et ipsum. Quisque at lacus. Etiam pellentesque, '
                         'enim porta pulvinar viverra, libero elit iaculis '
                         'justo, vitae convallis pede purus vel arcu. Morbi '
                         'aliquam lacus et urna. Donec commodo pellentesque '
                         'mi.')).text()
    assert txt == expected
    checkrest(txt)

def test_text_indented():
    expected = """\
This is a paragraph with some indentation. The indentation should be removed
and the lines split up nicely. This is still part of the first paragraph.
"""
    txt = Rest(Paragraph('This is a paragraph with some\n'
                         '    indentation. The indentation\n'
                         ' should be removed and the lines split up nicely.\n'
                         '\nThis is still part of the first paragraph.')
                         ).text()
    assert txt == expected
    checkrest(txt)

def test_text_strip():
    expected = "foo\n"
    txt = Rest(Paragraph(Text(' foo '))).text()
    assert txt == expected
    checkrest(txt)

def test_list():
    expected = "* a\n\n* b\n"
    txt = Rest(ListItem("a"), ListItem("b")).text()
    assert txt == expected
    checkrest(txt)

def test_list_item_multiple_args():
    expected = "* foo bar baz\n"
    txt = Rest(ListItem('foo', 'bar', 'baz')).text()
    assert txt == expected
    checkrest(txt)

def test_list_multiline():
    expected = """\
* Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Vestibulum
  malesuada eleifend leo. Sed faucibus commodo libero.

* Mauris elementum fringilla velit. Ut sem urna, aliquet sed, molestie at,
  viverra id, justo. In ornare lacinia turpis. Etiam et ipsum. Quisque at
  lacus.

* Etiam pellentesque, enim porta pulvinar viverra, libero elit iaculis justo,
  vitae convallis pede purus vel arcu. Morbi aliquam lacus et urna. Donec
  commodo pellentesque mi.
"""
    txt = Rest(ListItem('Lorem ipsum dolor sit amet, consectetuer adipiscing '
                        'elit. Vestibulum malesuada eleifend leo. Sed '
                        'faucibus commodo libero.'),
               ListItem('Mauris elementum fringilla velit. Ut sem urna, '
                        'aliquet sed, molestie at, viverra id, justo. In '
                        'ornare lacinia turpis. Etiam et ipsum. Quisque at '
                        'lacus.'),
               ListItem('Etiam pellentesque, enim porta pulvinar viverra, '
                        'libero elit iaculis justo, vitae convallis pede '
                        'purus vel arcu. Morbi aliquam lacus et urna. Donec '
                        'commodo pellentesque mi.')).text()
    assert txt == expected
    checkrest(txt)

def test_list_multiline_no_parent():
    expected = ("* test **strong**\n  thisisaverylongwordthatdoesntfiton"
                "thepreviouslineandthereforeshouldbeindented")
    txt = ListItem(Text('test'), Strong('strong'),
                   Text('thisisaverylongwordthatdoesntfitontheprevious'
                        'lineandthereforeshouldbeindented')).text()
    assert txt == expected
    checkrest(txt)

def test_ordered_list():
    expected = "#. foo\n\n#. bar\n\n#. baz\n"
    txt = Rest(OrderedListItem('foo'), OrderedListItem('bar'),
               OrderedListItem('baz')).text()
    assert txt == expected
    checkrest(txt)

def test_nested_lists():
    expected = """\
* foo

* bar

  + baz
"""
    txt = Rest(ListItem('foo'), ListItem('bar', ListItem('baz'))).text()
    assert txt == expected
    checkrest(txt)

def test_nested_nested_lists():
    expected = """\
* foo

  + bar

    - baz

  + qux

* quux
"""
    txt = Rest(ListItem('foo', ListItem('bar', ListItem('baz')),
                               ListItem('qux')), ListItem('quux')).text()
    print txt
    assert txt == expected
    checkrest(txt)

def test_definition_list():
    expected = """\
foo
  bar, baz and qux!

spam
  eggs, spam, spam, eggs, spam and spam...
"""
    txt = Rest(DListItem("foo", "bar, baz and qux!"),
               DListItem("spam", "eggs, spam, spam, eggs, spam and spam...")
               ).text()
    assert txt == expected
    checkrest(txt)

def test_nested_dlists():
    expected = """\
foo
  bar baz

  qux
    quux
"""
    txt = Rest(DListItem('foo', 'bar baz', DListItem('qux', 'quux'))).text()
    assert txt == expected

def test_nested_list_dlist():
    expected = """\
* foo

  foobar
    baz
"""
    txt = Rest(ListItem('foo', DListItem('foobar', 'baz'))).text()
    assert txt == expected

def test_transition():
    txt = Rest(Paragraph('foo'), Transition(), Paragraph('bar')).text()
    assert txt == 'foo\n\n%s\n\nbar\n' % ('-' * 79,)
    checkrest(txt)
    txt = Rest(Paragraph('foo'), Transition('+'), Paragraph('bar')).text()
    assert txt == 'foo\n\n%s\n\nbar\n' % ('+' * 79,)
    checkrest(txt)

    py.test.raises(ValueError, 'Rest(Transition(), Paragraph("foo")).text()')
    py.test.raises(ValueError, 'Rest(Paragraph("foo"), Transition()).text()')

def test_directive_simple():
    txt = Rest(Directive('image', 'images/foo.png')).text()
    assert txt == '.. image:: images/foo.png\n'

def test_directive_metadata():
    txt = Rest(Directive('image', 'images/foo.png',
                         width=200, height=150)).text()
    assert txt == ('.. image:: images/foo.png\n   :width: 200\n'
                   '   :height: 150\n')

def test_directive_multiline():
    txt = Rest(Directive('note', ('This is some string that is too long to '
                                  'fit on a single line, so it should be '
                                  'broken up.'))).text()
    assert txt == """\
.. note:: This is some string that is too long to fit on a single line, so it
   should be broken up.
"""

def test_directive_content():
    txt = Rest(Directive('image', 'foo.png', width=200, height=100,
                         content=[Paragraph('Some paragraph content.')])).text()
    assert txt == """\
.. image:: foo.png
   :width: 200
   :height: 100

   Some paragraph content.
"""

def test_title_following_links_empty_line():
    expected = """\
Foo, bar and `baz`_

Spam
====

Spam, eggs and spam.

.. _`baz`: http://www.baz.com

"""
    txt = Rest(Paragraph("Foo, bar and ", Link("baz", "http://www.baz.com")),
               Title('Spam'), Paragraph('Spam, eggs and spam.')).text()
    assert txt == expected
    checkrest(txt)

def test_nonstring_text():
    expected = """\
<foobar>
"""
    class FooBar(object):
        def __str__(self):
            return '<foobar>'
    txt = Rest(Paragraph(Text(FooBar()))).text()
    assert txt == expected

