import pytest


def test_yield_tests_deprecation(testdir):
    testdir.makepyfile("""
        def func1(arg, arg2):
            assert arg == arg2
        def test_gen():
            yield "m1", func1, 15, 3*5
            yield "m2", func1, 42, 6*7
    """)
    result = testdir.runpytest('-ra')
    result.stdout.fnmatch_lines([
        '*yield tests are deprecated, and scheduled to be removed in pytest 4.0*',
        '*2 passed*',
    ])


def test_funcarg_prefix_deprecation(testdir):
    testdir.makepyfile("""
        def pytest_funcarg__value():
            return 10

        def test_funcarg_prefix(value):
            assert value == 10
    """)
    result = testdir.runpytest('-ra')
    result.stdout.fnmatch_lines([
        ('WC1 None pytest_funcarg__value: '
         'declaring fixtures using "pytest_funcarg__" prefix is deprecated '
         'and scheduled to be removed in pytest 4.0.  '
         'Please remove the prefix and use the @pytest.fixture decorator instead.'),
        '*1 passed*',
    ])


def test_pytest_setup_cfg_deprecated(testdir):
    testdir.makefile('.cfg', setup='''
        [pytest]
        addopts = --verbose
    ''')
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*pytest*section in setup.cfg files is deprecated*use*tool:pytest*instead*'])


def test_str_args_deprecated(tmpdir, testdir):
    """Deprecate passing strings to pytest.main(). Scheduled for removal in pytest-4.0."""
    from _pytest.main import EXIT_NOTESTSCOLLECTED
    warnings = []

    class Collect:
        def pytest_logwarning(self, message):
            warnings.append(message)

    ret = pytest.main("%s -x" % tmpdir, plugins=[Collect()])
    testdir.delete_loaded_modules()
    msg = ('passing a string to pytest.main() is deprecated, '
           'pass a list of arguments instead.')
    assert msg in warnings
    assert ret == EXIT_NOTESTSCOLLECTED


def test_getfuncargvalue_is_deprecated(request):
    pytest.deprecated_call(request.getfuncargvalue, 'tmpdir')


def test_resultlog_is_deprecated(testdir):
    result = testdir.runpytest('--help')
    result.stdout.fnmatch_lines(['*DEPRECATED path for machine-readable result log*'])

    testdir.makepyfile('''
        def test():
            pass
    ''')
    result = testdir.runpytest('--result-log=%s' % testdir.tmpdir.join('result.log'))
    result.stdout.fnmatch_lines(['*--result-log is deprecated and scheduled for removal in pytest 4.0*'])
