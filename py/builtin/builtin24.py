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

try:
    sorted = sorted
except NameError:
    builtin_cmp = cmp # need to use cmp as keyword arg

    def sorted(iterable, cmp=None, key=None, reverse=0):
        use_cmp = None
        if key is not None:
            if cmp is None:
                def use_cmp(x, y):
                    return builtin_cmp(x[0], y[0])
            else:
                def use_cmp(x, y):
                    return cmp(x[0], y[0])
            l = [(key(element), element) for element in iterable]
        else:
            if cmp is not None:
                use_cmp = cmp
            l = list(iterable)
        if use_cmp is not None:
            l.sort(use_cmp)
        else:
            l.sort()
        if reverse:
            l.reverse()
        if key is not None:
            return [element for (_, element) in l]
        return l

try:
    set, frozenset = set, frozenset
except NameError:
    from sets import set, frozenset 

# pass through
enumerate = enumerate 
