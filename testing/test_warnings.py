import pytest


@pytest.fixture
def pyfile_with_warnings(testdir):
    testdir.makepyfile('''
        import warnings
        def test_func():
            warnings.warn(PendingDeprecationWarning("functionality is pending deprecation"))
            warnings.warn(DeprecationWarning("functionality is deprecated"))
    ''')


def test_normal_flow(testdir, pyfile_with_warnings):
    result = testdir.runpytest()
    result.stdout.fnmatch_lines([
        '*== pytest-warning summary ==*',

        'WW0 in *test_normal_flow.py:1 the following warning was recorded:',
        ' test_normal_flow.py:3: PendingDeprecationWarning: functionality is pending deprecation',
        '  warnings.warn(PendingDeprecationWarning("functionality is pending deprecation"))',

        'WW0 in *test_normal_flow.py:1 the following warning was recorded:',
        ' test_normal_flow.py:4: DeprecationWarning: functionality is deprecated',
        '  warnings.warn(DeprecationWarning("functionality is deprecated"))',
        '* 1 passed, 2 pytest-warnings*',
    ])


@pytest.mark.parametrize('method', ['cmdline', 'ini'])
def test_as_errors(testdir, pyfile_with_warnings, method):
    args = ('-W', 'error') if method == 'cmdline' else ()
    if method == 'ini':
        testdir.makeini('''
            [pytest]
            filterwarnings= error
            ''')
    result = testdir.runpytest(*args)
    result.stdout.fnmatch_lines([
        'E       PendingDeprecationWarning: functionality is pending deprecation',
        'test_as_errors.py:3: PendingDeprecationWarning',
        '* 1 failed in *',
    ])


@pytest.mark.parametrize('method', ['cmdline', 'ini'])
def test_ignore(testdir, pyfile_with_warnings, method):
    args = ('-W', 'ignore') if method == 'cmdline' else ()
    if method == 'ini':
        testdir.makeini('''
        [pytest]
        filterwarnings= ignore
        ''')

    result = testdir.runpytest(*args)
    result.stdout.fnmatch_lines([
        '* 1 passed in *',
    ])
    assert 'pytest-warning summary' not in result.stdout.str()

