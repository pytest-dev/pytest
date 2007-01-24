from __future__ import generators
try:
    enumerate = enumerate
except NameError:
    def enumerate(iterable):
        i = 0
        for x in iterable:
            yield i, x
            i += 1
