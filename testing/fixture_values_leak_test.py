"""Ensure that fixture objects are properly destroyed by the garbage collector at the end of their expected
life-times (#2981).

This comes from the old acceptance_test.py::test_fixture_values_leak(testdir):
This used pytester before but was not working when using pytest_assert_reprcompare
because pytester tracks hook calls and it would hold a reference (ParsedCall object),
preventing garbage collection

<ParsedCall 'pytest_assertrepr_compare'(**{
    'config': <_pytest.config.Config object at 0x0000019C18D1C2B0>,
    'op': 'is',
    'left': SomeObj(name='local-fixture'),
    'right': SomeObj(name='local-fixture')})>
"""
import attr
import gc
import pytest
import weakref


@attr.s
class SomeObj(object):
    name = attr.ib()


fix_of_test1_ref = None
session_ref = None


@pytest.fixture(scope="session")
def session_fix():
    global session_ref
    obj = SomeObj(name="session-fixture")
    session_ref = weakref.ref(obj)
    return obj


@pytest.fixture
def fix(session_fix):
    global fix_of_test1_ref
    obj = SomeObj(name="local-fixture")
    fix_of_test1_ref = weakref.ref(obj)
    return obj


def test1(fix):
    assert fix_of_test1_ref() is fix


def test2():
    gc.collect()
    # fixture "fix" created during test1 must have been destroyed by now
    assert fix_of_test1_ref() is None
