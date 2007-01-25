""" functional test for apigen.py

    script to build api + source docs from py.test
"""

import py

def setup_fs_project():
    temp = py.test.ensuretemp('apigen_functional')
    temp.ensure("pkg/func.py").write(py.code.Source("""\
        def func(arg1):
            "docstring"

        def func_2(arg1, arg2):
            return arg1(arg2)
    """))
    temp.ensure('pkg/sometestclass.py').write(py.code.Source("""\
        class SomeTestClass(object):
            " docstring sometestclass "
            def __init__(self, somevar):
                self.somevar = somevar
                
            def get_somevar(self):
                " get_somevar docstring "
                return self.somevar
    """))
    temp.ensure('pkg/sometestsubclass.py').write(py.code.Source("""\
        from sometestclass import SomeTestClass
        class SomeTestSubClass(SomeTestClass):
            " docstring sometestsubclass "
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
            'main.func': ("./func.py", "func_2"),
            'main.SomeTestClass': ('./sometestclass.py', 'SomeTestClass'),
            'main.SomeTestSubClass': ('./sometestsubclass.py',
                                      'SomeTestSubClass'),
        })
    """))
    temp.ensure('pkg/test/test_pkg.py').write(py.code.Source("""\
        import py
        py.std.sys.path.insert(0,
            py.magic.autopath().dirpath().dirpath().dirpath().strpath)
        import pkg

        # this mainly exists to provide some data to the tracer
        def test_pkg():
            s = pkg.main.SomeTestClass(10)
            assert s.get_somevar() == 10
            s = pkg.main.SomeTestClass('10')
            assert s.get_somevar() == '10'
            s = pkg.main.SomeTestSubClass(10)
            assert s.get_somevar() == 11
            s = pkg.main.SomeTestSubClass('10')
            py.test.raises(TypeError, 's.get_somevar()')
            assert pkg.main.sub.func(10) is None
            assert pkg.main.sub.func(20) is None
            s = pkg.main.func(pkg.main.SomeTestClass, 10)
            assert isinstance(s, pkg.main.SomeTestClass)
    """))
    return temp, 'pkg'

def test_apigen_functional():
    fs_root, package_name = setup_fs_project()
    tempdir = py.test.ensuretemp('test_apigen_functional_results')
    pydir = py.magic.autopath().dirpath().dirpath().dirpath()
    pkgdir = fs_root.join('pkg')
    if py.std.sys.platform == 'win32':
        cmd = 'set APIGEN_TARGET=%s && python "%s/bin/py.test"' % (tempdir,
                                                                   pydir)
    else:
        cmd = 'APIGEN_TARGET="%s" "%s/bin/py.test"' % (tempdir, pydir)
    try:
        output = py.process.cmdexec('%s --apigen="%s/apigen.py" "%s"' % (
                                        cmd, pydir.join('apigen'),
                                        pkgdir))
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
    assert '<a href="main.SomeTestClass.html">SomeTestClass</a>' in html
    # XXX not linking to method files anymore
    #sometestclass_init_api = apidir.join('main.SomeTestClass.__init__.html')
    #assert sometestclass_init_api.check(file=True)
    #assert sometestclass_init_api.read().find(
    #        '<a href="main.SomeTestClass.__init__.html">__init__</a>') > -1
    namespace_api = apidir.join('main.html')
    assert namespace_api.check(file=True)
    html = namespace_api.read()
    assert '<a href="main.SomeTestClass.html">SomeTestClass</a>' in html

    sourcedir = tempdir.join('source')
    assert sourcedir.check(dir=True)
    sometestclass_source = sourcedir.join('sometestclass.py.html')
    assert sometestclass_source.check(file=True)
    html = sometestclass_source.read()
    assert '<div class="project_title">sources for sometestclass.py</div>' in html

    # XXX later...
    #index = sourcedir.join('index.html')
    #assert index.check(file=True)
    #html = index.read()
    #assert '<a href="main/index.html">main</a>' in html

