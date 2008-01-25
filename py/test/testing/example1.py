
def f1():
    f2()

def f2():
    pass

def g1():
    g2()

def g2():
    raise ValueError()
