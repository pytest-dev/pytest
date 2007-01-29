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

def test_build_navitem_html():
    l = Linker()
    l.set_link('spam.eggs.foo', 'foo.html')
    h = htmlgen.build_navitem_html(l, 'foo', 'spam.eggs.foo', 0, False)
    assert unicode(h) == u'<div><a href="foo.html">foo</a></div>'
    h = htmlgen.build_navitem_html(l, 'bar', 'spam.eggs.foo', 1, True)
    assert unicode(h) == (u'<div class="selected">\xa0\xa0'
                          u'<a href="foo.html">bar</a></div>')

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

