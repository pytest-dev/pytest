""" functional test for apigen.py

    script to build api + source docs from py.test
"""

import py
from py.__.apigen import apigen
py.test.skip("Apigen functionality temporarily disabled")

def setup_module(mod):
    if py.std.sys.platform == "win32":
        py.test.skip("not supported with win32 yet")

def setup_fs_project(name):
    temp = py.test.ensuretemp(name)
    assert temp.listdir() == []
    temp.ensure("pak/func.py").write(py.code.Source("""\
        def func(arg1):
            "docstring"

        def func_2(arg1, arg2):
            return arg1(arg2)
    """))
    temp.ensure('pak/sometestclass.py').write(py.code.Source("""\
        class SomeTestClass(object):
            " docstring sometestclass "
            someattr = 'somevalue'
            def __init__(self, somevar):
                self.somevar = somevar
                
            def get_somevar(self):
                " get_somevar docstring "
                return self.somevar
            
            def get_some_source(self):
                ret = py.code.Source('''\\
                    def foo():
                      return 'bar'
                ''')
                return ret

    """))
    temp.ensure('pak/sometestsubclass.py').write(py.code.Source("""\
        from sometestclass import SomeTestClass
        class SomeTestSubClass(SomeTestClass):
            " docstring sometestsubclass "
            def get_somevar(self):
                return self.somevar + 1
    """))
    temp.ensure('pak/somenamespace.py').write(py.code.Source("""\
        def foo():
            return 'bar'
        def baz(qux):
            return qux
        def _hidden():
            return 'quux'
    """))
    temp.ensure("pak/__init__.py").write(py.code.Source("""\
        '''pkg docstring'''
        from py.initpkg import initpkg
        initpkg(__name__,
                long_description=globals()['__doc__'],
                exportdefs={'main.sub.func': ("./func.py", "func"),
                            'main.func': ("./func.py", "func_2"),
                            'main.SomeTestClass': ('./sometestclass.py',
                                                   'SomeTestClass'),
                            'main.SomeTestSubClass': ('./sometestsubclass.py',
                                                      'SomeTestSubClass'),
                            'somenamespace': ('./somenamespace.py', '*')})
    """))
    temp.ensure('apigen.py').write(py.code.Source("""\
        import py
        py.std.sys.path.insert(0,
            py.magic.autopath().dirpath().dirpath().dirpath().strpath)
        from py.__.apigen.apigen import build, \
            get_documentable_items_pkgdir as get_documentable_items
    """))
    temp.ensure('pak/test/test_pak.py').write(py.code.Source("""\
        import py
        py.std.sys.path.insert(0,
            py.magic.autopath().dirpath().dirpath().dirpath().strpath)
        import pak

        # this mainly exists to provide some data to the tracer
        def test_pak():
            s = pak.main.SomeTestClass(10)
            assert s.get_somevar() == 10
            s = pak.main.SomeTestClass('10')
            assert s.get_somevar() == '10'
            s = pak.main.SomeTestSubClass(10)
            assert s.get_somevar() == 11
            s = pak.main.SomeTestSubClass('10')
            py.test.raises(TypeError, 's.get_somevar()')
            assert pak.main.sub.func(10) is None
            assert pak.main.sub.func(20) is None
            s = pak.main.func(pak.main.SomeTestClass, 10)
            assert isinstance(s, pak.main.SomeTestClass)

            # some nice things to confuse the tracer/storage
            source = py.code.Source('''\
                pak.main.sub.func(10)
            ''')
            c = compile(str(source), '<test>', 'exec')
            exec c in globals()

            assert pak.somenamespace._hidden() == 'quux'

            # this just to see a multi-level stack in the docs
            def foo():
                return pak.main.sub.func(10)
            assert foo() is None
    """))
    return temp, 'pak'

def test_get_documentable_items():
    fs_root, package_name = setup_fs_project('test_get_documentable_items')
    pkgname, documentable = apigen.get_documentable_items_pkgdir(
                                               fs_root.join(package_name))
    assert pkgname == 'pak'
    keys = documentable.keys()
    keys.sort()
    assert keys ==  [
        'main.SomeTestClass', 'main.SomeTestSubClass', 'main.func',
        'main.sub.func', 'somenamespace.baz', 'somenamespace.foo']

def test_apigen_functional():
    #if py.std.sys.platform == "win32":
    #    py.test.skip("XXX test fails on windows")
    fs_root, package_name = setup_fs_project('test_apigen_functional')
    tempdir = py.test.ensuretemp('test_apigen_functional_results')
    pydir = py.magic.autopath().dirpath().dirpath().dirpath()
    pakdir = fs_root.join('pak')
    if py.std.sys.platform == 'win32':
        cmd = ('set APIGENPATH=%s && set PYTHONPATH=%s && '
               'python "%s/bin/py.test"') % (tempdir, fs_root, pydir)
    else:
        cmd = ('APIGENPATH="%s" PYTHONPATH="%s" '
               'python "%s/bin/py.test"') % (tempdir, fs_root, pydir)
    try:
        output = py.process.cmdexec('%s --apigen="%s/apigen.py" "%s"' % (
                                        cmd, fs_root, pakdir))
    except py.error.Error, e:
        print e.out
        raise
    assert output.lower().find('traceback') == -1

    # just some quick content checks
    apidir = tempdir.join('api')
    assert apidir.check(dir=True)
    sometestclass_api = apidir.join('main.SomeTestClass.html')
    assert sometestclass_api.check(file=True)
    html = sometestclass_api.read()
    print html
    assert '<a href="main.SomeTestClass.html">SomeTestClass</a>' in html
    assert 'someattr: <em>somevalue</em>' in html
    
    namespace_api = apidir.join('main.html')
    assert namespace_api.check(file=True)
    html = namespace_api.read()
    assert '<a href="main.SomeTestClass.html">SomeTestClass</a>' in html
    index = apidir.join('index.html')
    assert index.check(file=True)
    html = index.read()
    assert 'pkg docstring' in html

    sourcedir = tempdir.join('source')
    assert sourcedir.check(dir=True)
    sometestclass_source = sourcedir.join('sometestclass.py.html')
    assert sometestclass_source.check(file=True)
    html = sometestclass_source.read()
    assert '<div class="project_title">sources for sometestclass.py</div>' in html

    index = sourcedir.join('index.html')
    assert index.check(file=True)
    html = index.read()
    print html
    assert '<a href="test/index.html">test</a>' in html
    assert 'href="../../py/doc/home.html"'

