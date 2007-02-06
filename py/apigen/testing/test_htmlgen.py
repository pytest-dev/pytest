import py
from py.__.apigen import htmlgen
from py.__.apigen.linker import Linker

def test_create_namespace_tree():
    tree = htmlgen.create_namespace_tree(['foo.bar.baz'])
    assert tree == {'': ['foo'],
                    'foo': ['foo.bar'],
                    'foo.bar': ['foo.bar.baz']}
    tree = htmlgen.create_namespace_tree(['foo.bar.baz', 'foo.bar.qux'])
    assert tree == {'': ['foo'],
                    'foo': ['foo.bar'],
                    'foo.bar': ['foo.bar.baz', 'foo.bar.qux']}
    tree = htmlgen.create_namespace_tree(['pkg.sub.func',
                                          'pkg.SomeClass',
                                          'pkg.SomeSubClass'])
    assert tree == {'': ['pkg'],
                    'pkg.sub': ['pkg.sub.func'],
                    'pkg': ['pkg.sub', 'pkg.SomeClass',
                            'pkg.SomeSubClass']}

def test_source_dirs_files():
    temp = py.test.ensuretemp('test_source_dirs_files')
    temp.join('dir').ensure(dir=True)
    temp.join('dir/file1.py').ensure(file=True)
    temp.join('dir/file2.pyc').ensure(file=True)
    temp.join('dir/file3.c').ensure(file=True)
    temp.join('dir/.hidden_file').ensure(file=True)
    temp.join('dir/sub').ensure(dir=True)
    temp.join('dir/.hidden_dir').ensure(dir=True)
    dirs, files = htmlgen.source_dirs_files(temp.join('dir'))
    dirnames = py.builtin.sorted([d.basename for d in dirs])
    filenames = py.builtin.sorted([f.basename for f in files])
    assert dirnames == ['sub']
    assert filenames == ['file1.py', 'file3.c']

def test_deindent():
    assert htmlgen.deindent('foo\n\n    bar\n    ') == 'foo\n\nbar\n'
    assert htmlgen.deindent(' foo\n\n    bar\n    ') == 'foo\n\nbar\n'
    assert htmlgen.deindent('foo\n\n    bar\n    baz') == 'foo\n\nbar\nbaz\n'
    assert htmlgen.deindent(' foo\n\n    bar\n      baz\n') == (
        'foo\n\nbar\n  baz\n')
    assert htmlgen.deindent('foo\n\n      bar\n    baz\n') == (
        'foo\n\n  bar\nbaz\n')

def test_enumerate_and_color():
    colored = htmlgen.enumerate_and_color(['def foo():', '  print "bar"'], 0,
                                          'ascii')
    div = py.xml.html.div(*colored).unicode(indent=0)
    print repr(div)
    assert div == (u'<div>'
                    '<table style="float: left">'
                    '<tbody>'
                    '<tr><td class="lineno">1</td></tr>'
                    '<tr><td class="lineno">2</td></tr>'
                    '</tbody>'
                    '</table>'
                    '<table>'
                    '<tbody>'
                    '<tr><td class="code">'
                    '<span class="alt_keyword">def</span> foo():'
                    '</td></tr>'
                    '<tr><td class="code">'
                    '  <span class="keyword">print</span>'
                    ' <span class="string">&quot;bar&quot;</span>'
                    '</td></tr>'
                    '</tbody>'
                    '</table>'
                    '</div>')

def test_enumerate_and_color_multiline():
    colored = htmlgen.enumerate_and_color(['code = """\\', 'foo bar', '"""'],
                                          0, 'ascii')
    div = py.xml.html.div(*colored).unicode(indent=0)
    print repr(div)
    assert div == (u'<div>'
                    '<table style="float: left">'
                    '<tbody>'
                    '<tr><td class="lineno">1</td></tr>'
                    '<tr><td class="lineno">2</td></tr>'
                    '<tr><td class="lineno">3</td></tr>'
                    '</tbody>'
                    '</table>'
                    '<table>'
                    '<tbody>'
                    '<tr><td class="code">'
                    'code = <span class="string">&quot;&quot;&quot;\\</span>'
                    '</td></tr>'
                    '<tr><td class="code">'
                    '<span class="string">foo bar</span>'
                    '</td></tr>'
                    '<tr><td class="code">'
                    '<span class="string">&quot;&quot;&quot;</span>'
                    '</td></tr>'
                    '</tbody>'
                    '</table>'
                    '</div>')

def test_show_property():
    assert htmlgen.show_property('foo')
    assert not htmlgen.show_property('_foo')
    assert htmlgen.show_property('__foo__')
    assert not htmlgen.show_property('__doc__')
    assert not htmlgen.show_property('__dict__')
    assert not htmlgen.show_property('__name__')
    assert not htmlgen.show_property('__class__')

