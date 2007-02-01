import py
try:
    from py.magic import greenlet
except (ImportError, RuntimeError), e:
    py.test.skip(str(e))



class genlet(greenlet):

    def __init__(self, *args, **kwds):
        self.args = args
        self.kwds = kwds

    def run(self):
        fn, = self.fn
        fn(*self.args, **self.kwds)

    def __iter__(self):
        return self

    def next(self):
        self.parent = greenlet.getcurrent()
        result = self.switch()
        if self:
            return result
        else:
            raise StopIteration

def Yield(value):
    g = greenlet.getcurrent()
    while not isinstance(g, genlet):
        if g is None:
            raise RuntimeError, 'yield outside a genlet'
        g = g.parent
    g.parent.switch(value)

def generator(func):
    class generator(genlet):
        fn = (func,)
    return generator

# ____________________________________________________________

def test_generator():
    seen = []

    def g(n):
        for i in range(n):
            seen.append(i)
            Yield(i)
    g = generator(g)

    for k in range(3):
        for j in g(5):
            seen.append(j)

    assert seen == 3 * [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
