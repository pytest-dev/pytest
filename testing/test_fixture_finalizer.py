"""Tests for fixtures with different scoping."""
import py.code


def test_fixture_finalizer(testdir):
    testdir.makeconftest("""
    import pytest

    @pytest.fixture
    def browser(request):

        def finalize():
            print 'Finalized'
        request.addfinalizer(finalize)
        return {}
    """)
    b = testdir.mkdir("subdir")
    b.join("test_overriden_fixture_finalizer.py").write(py.code.Source("""
    import pytest
    @pytest.fixture
    def browser(browser):
        browser['visited'] = True
        return browser

    def test_browser(browser):
        assert browser['visited'] is True
    """))
    reprec = testdir.runpytest("-s")
    for test in ['test_browser']:
        reprec.stdout.fnmatch_lines('Finalized')
