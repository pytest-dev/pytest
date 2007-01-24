from __future__ import generators
import py
try:
    from py.magic import greenlet
except (ImportError, RuntimeError), e:
    py.test.skip(str(e))

class genlet(greenlet):

    def __init__(self, *args, **kwds):
        self.args = args
        self.kwds = kwds
        self.child = None
        
    def run(self):
        fn, = self.fn
        fn(*self.args, **self.kwds)

    def __iter__(self):
        return self

    def set_child(self, child):
        self.child = child

    def next(self):
        if self.child:
            child = self.child
            while child.child:
                tmp = child
                child = child.child
                tmp.child = None

            result = child.switch()
        else:
            self.parent = greenlet.getcurrent()            
            result = self.switch()
        
        if self:
            return result
        else:
            raise StopIteration

def Yield(value, level = 1):
    g = greenlet.getcurrent()
    
    while level != 0:
        if not isinstance(g, genlet):
            raise RuntimeError, 'yield outside a genlet'
        if level > 1:
            g.parent.set_child(g)
        g = g.parent
        level -= 1

    g.switch(value)
    
def Genlet(func):
    class Genlet(genlet):
        fn = (func,)
    return Genlet

# ____________________________________________________________

def g1(n, seen):
    for i in range(n):
        seen.append(i+1)
        yield i

def g2(n, seen):
    for i in range(n):
        seen.append(i+1)
        Yield(i)

g2 = Genlet(g2)

def nested(i):
    Yield(i)

def g3(n, seen):
    for i in range(n):
        seen.append(i+1)
        nested(i)
g3 = Genlet(g3)

def test_genlet_simple():

    for g in [g1, g2, g3]:
        seen = []
        for k in range(3):
            for j in g(5, seen):
                seen.append(j)
                
        assert seen == 3 * [1, 0, 2, 1, 3, 2, 4, 3, 5, 4]

def test_genlet_bad():
    try:
        Yield(10)
    except RuntimeError:
        pass
    
test_genlet_bad()
test_genlet_simple()
test_genlet_bad()

def a(n):
    if n == 0:
        return
    for ii in ax(n-1):
        Yield(ii)
    Yield(n)
ax = Genlet(a)

def test_nested_genlets():
    seen = []
    for ii in ax(5):
        seen.append(ii)

test_nested_genlets()

def perms(l):
    if len(l) > 1:
        for e in l:
            # No syntactical sugar for generator expressions
            [Yield([e] + p) for p in perms([x for x in l if x!=e])]
    else:
        Yield(l)

perms = Genlet(perms)

def test_perms():
    gen_perms = perms(range(4))
    permutations = list(gen_perms)
    assert len(permutations) == 4*3*2*1
    assert [0,1,2,3] in permutations
    assert [3,2,1,0] in permutations
    res = []
    for ii in zip(perms(range(4)), perms(range(3))):
        res.append(ii)
    # XXX Test to make sure we are working as a generator expression
test_perms()


def gr1(n):
    for ii in range(1, n):
        Yield(ii)
        Yield(ii * ii, 2)

gr1 = Genlet(gr1)

def gr2(n, seen):
    for ii in gr1(n):
        seen.append(ii)

gr2 = Genlet(gr2)

def test_layered_genlets():
    seen = []
    for ii in gr2(5, seen):
        seen.append(ii)
    assert seen == [1, 1, 2, 4, 3, 9, 4, 16]

test_layered_genlets()
