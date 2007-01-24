from py.builtin import reversed
from py.test import raises

def test_reversed():
    r = reversed("hello")
    assert iter(r) is r
    assert r.next() == "o"
    assert r.next() == "l"
    assert r.next() == "l"
    assert r.next() == "e"
    assert r.next() == "h"
    raises(StopIteration, r.next)
    assert list(reversed(list(reversed("hello")))) == ['h','e','l','l','o']
    raises(TypeError, reversed, reversed("hello"))
