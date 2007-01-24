from __future__ import generators
try:
    reversed = reversed
except NameError:

    def reversed(sequence):
        """reversed(sequence) -> reverse iterator over values of the sequence

        Return a reverse iterator
        """
        if hasattr(sequence, '__reversed__'):
            return sequence.__reversed__()
        if not hasattr(sequence, '__getitem__'):
            raise TypeError("argument to reversed() must be a sequence")
        return reversed_iterator(sequence)


    class reversed_iterator(object):

        def __init__(self, seq):
            self.seq = seq
            self.remaining = len(seq)

        def __iter__(self):
            return self

        def next(self):
            i = self.remaining
            if i > 0:
                i -= 1
                item = self.seq[i]
                self.remaining = i
                return item
            raise StopIteration

        def __length_hint__(self):
            return self.remaining
