builtin_cmp = cmp # need to use cmp as keyword arg

def _sorted(iterable, cmp=None, key=None, reverse=0):
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
    #print l
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
    sorted = sorted
except NameError:
    sorted = _sorted
