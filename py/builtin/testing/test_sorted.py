from __future__ import generators
import py
from py.__.builtin.sorted import _sorted

def test_sorted():
    for s in [_sorted, py.builtin.sorted]:
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

