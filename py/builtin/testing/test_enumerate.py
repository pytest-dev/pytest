import sys
import py

def test_enumerate():
    l = [0,1,2]
    for i,x in py.builtin.enumerate(l):
        assert i == x
