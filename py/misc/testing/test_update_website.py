import py
import sys

here = py.magic.autopath().dirpath()
update_website = here.join('../../bin/_update_website.py').pyimport()

def test_rsync():
    temp = py.test.ensuretemp('update_website_rsync')
    pkgpath = temp.join('pkg')
    apipath = temp.join('apigen')
    pkgpath.ensure('foo/bar.txt', file=True).write('baz')
    pkgpath.ensure('spam/eggs.txt', file=True).write('spam')
    apipath.ensure('api/foo.html', file=True).write('<html />')
    apipath.ensure('source/spam.html', file=True).write('<html />')

    rsyncpath = temp.join('rsync')
    assert not rsyncpath.check()
    gateway = py.execnet.PopenGateway()
    update_website.rsync(pkgpath, apipath, gateway, rsyncpath.strpath)
    assert rsyncpath.check(dir=True)
    assert rsyncpath.join('pkg').check(dir=True)
    assert rsyncpath.join('pkg/spam/eggs.txt').read() == 'spam'
    assert rsyncpath.join('apigen').check(dir=True)
    assert rsyncpath.join('apigen/api/foo.html').read() == '<html />'

def setup_pkg(testname):
    temp = py.test.ensuretemp(testname)
    pkgpath = temp.ensure('pkg', dir=True)
    pyfile = pkgpath.ensure('mod.py').write(py.code.Source("""
        def foo(x):
            return x + 1
    """))
    testfile = pkgpath.ensure('test/test_mod.py').write(py.code.Source("""
        from pkg.sub import foo
        def test_foo():
            assert foo(1) == 2
    """))
    initfile = pkgpath.ensure('__init__.py').write(py.code.Source("""\
        import py
        from py.__.initpkg import initpkg
        initpkg(__name__, exportdefs={
            'sub.foo': ('./mod.py', 'foo'),
        })
    """))
    return pkgpath

def test_run_tests():
    if py.std.sys.platform == "win32":
        py.test.skip("update_website is not supposed to be run from win32")
    pkgpath = setup_pkg('update_website_run_tests')
    errors = update_website.run_tests(pkgpath)
    assert not errors
    assert pkgpath.join('../apigen').check(dir=True)
    assert pkgpath.join('../apigen/api/sub.foo.html').check(file=True)

def test_run_tests_failure():
    if py.std.sys.platform == "win32":
        py.test.skip("update_website is not supposed to be run from win32")
    pkgpath = setup_pkg('update_website_run_tests_failure')
    assert not pkgpath.join('../apigen').check(dir=True)
    pkgpath.ensure('../apigen', file=True)
    errors = update_website.run_tests(pkgpath, '> /dev/null 2>&1')
    assert errors # some error message

