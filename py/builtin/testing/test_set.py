# some small tests to see whether sets are there and work

from py.builtin import set, frozenset

def test_simple():
    s = set([1, 2, 3, 4])
    assert s == set([3, 4, 2, 1])
    s1 = s.union(set([5, 6]))
    assert 5 in s1
    assert 1 in s1

def test_frozenset():
    s = set([frozenset([0, 1]), frozenset([1, 0])])
    assert len(s) == 1
