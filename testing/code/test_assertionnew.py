import sys

import py
from py._code._assertionnew import interpret


def getframe():
    """Return the frame of the caller as a py.code.Frame object"""
    return py.code.Frame(sys._getframe(1))


def setup_module(mod):
    py.code.patch_builtins(assertion=True, compile=False)


def teardown_module(mod):
    py.code.unpatch_builtins(assertion=True, compile=False)


def test_assert_simple():
    # Simply test that this way of testing works
    a = 0
    b = 1
    r = interpret('assert a == b', getframe())
    assert r == 'assert 0 == 1'


def test_assert_list():
    r = interpret('assert [0, 1] == [0, 2]', getframe())
    msg = ('assert [0, 1] == [0, 2]\n'
           '  First differing item 1: 1 != 2\n'
           '  - [0, 1]\n'
           '  ?     ^\n'
           '  + [0, 2]\n'
           '  ?     ^')
    print r
    assert r == msg


def test_assert_string():
    r = interpret('assert "foo and bar" == "foo or bar"', getframe())
    msg = ("assert 'foo and bar' == 'foo or bar'\n"
           "  - foo and bar\n"
           "  ?     ^^^\n"
           "  + foo or bar\n"
           "  ?     ^^")
    print r
    assert r == msg


def test_assert_multiline_string():
    a = 'foo\nand bar\nbaz'
    b = 'foo\nor bar\nbaz'
    r = interpret('assert a == b', getframe())
    msg = ("assert 'foo\\nand bar\\nbaz' == 'foo\\nor bar\\nbaz'\n"
           '    foo\n'
           '  - and bar\n'
           '  + or bar\n'
           '    baz')
    print r
    assert r == msg


def test_assert_dict():
    a = {'a': 0, 'b': 1}
    b = {'a': 0, 'c': 2}
    r = interpret('assert a == b', getframe())
    msg = ("assert {'a': 0, 'b': 1} == {'a': 0, 'c': 2}\n"
           "  - {'a': 0, 'b': 1}\n"
           "  ?           ^   ^\n"
           "  + {'a': 0, 'c': 2}\n"
           "  ?           ^   ^")
    print r
    assert r == msg
