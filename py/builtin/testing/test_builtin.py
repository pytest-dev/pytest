import sys
import py
from py.builtin import set, frozenset, reversed, sorted

def test_enumerate():
    l = [0,1,2]
    for i,x in enumerate(l):
        assert i == x

def test_BaseException():
    assert issubclass(IndexError, py.builtin.BaseException)
    assert issubclass(Exception, py.builtin.BaseException)
    assert issubclass(KeyboardInterrupt, py.builtin.BaseException)

    class MyRandomClass(object):
        pass
    assert not issubclass(MyRandomClass, py.builtin.BaseException)

    assert py.builtin.BaseException.__module__ == 'exceptions'
    assert Exception.__name__ == 'Exception'


def test_GeneratorExit():
    assert py.builtin.GeneratorExit.__module__ == 'exceptions'
    assert issubclass(py.builtin.GeneratorExit, py.builtin.BaseException)

def test_reversed():
    reversed = py.builtin.reversed
    r = reversed("hello")
    assert iter(r) is r
    assert r.next() == "o"
    assert r.next() == "l"
    assert r.next() == "l"
    assert r.next() == "e"
    assert r.next() == "h"
    py.test.raises(StopIteration, r.next)
    assert list(reversed(list(reversed("hello")))) == ['h','e','l','l','o']
    py.test.raises(TypeError, reversed, reversed("hello"))

def test_simple():
    s = set([1, 2, 3, 4])
    assert s == set([3, 4, 2, 1])
    s1 = s.union(set([5, 6]))
    assert 5 in s1
    assert 1 in s1

def test_frozenset():
    s = set([frozenset([0, 1]), frozenset([1, 0])])
    assert len(s) == 1

def test_sorted():
    for s in [py.builtin.sorted]:
        def test():
            assert s([3, 2, 1]) == [1, 2, 3]
            assert s([1, 2, 3], reverse=True) == [3, 2, 1]
            l = s([1, 2, 3, 4, 5, 6], key=lambda x: x % 2)
            assert l == [2, 4, 6, 1, 3, 5]
            l = s([1, 2, 3, 4], cmp=lambda x, y: -cmp(x, y))
            assert l == [4, 3, 2, 1]
            l = s([1, 2, 3, 4], cmp=lambda x, y: -cmp(x, y),
                        key=lambda x: x % 2)
            assert l == [1, 3, 2, 4]

            def compare(x, y):
                assert type(x) == str
                assert type(y) == str
                return cmp(x, y)
            data = 'The quick Brown fox Jumped over The lazy Dog'.split()
            s(data, cmp=compare, key=str.lower)
        yield test


def test_print_simple():
    from py.builtin import print_
    f = py.io.TextIO()
    print_("hello", "world", file=f)
    s = f.getvalue()
    assert s == "hello world\n"
    py.test.raises(TypeError, "print_(hello=3)")

def test_reraise():
    from py.builtin import _reraise 
    try:
        raise Exception()
    except Exception:
        cls, val, tb = sys.exc_info()
    excinfo = py.test.raises(Exception, "_reraise(cls, val, tb)")
   
def test_exec():
    l = []
    py.builtin.exec_("l.append(1)")
    assert l == [1]
    d = {}
    py.builtin.exec_("x=4", d)
    assert d['x'] == 4
