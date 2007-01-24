from StringIO import StringIO

def pickletest(mod):
    f1 = StringIO()
    f2 = StringIO()

    pickler1 = mod.Pickler(f1)
    unpickler1 = mod.Unpickler(f2)

    pickler2 = mod.Pickler(f2)
    unpickler2 = mod.Unpickler(f1)

    #pickler1.memo = unpickler1.memo = {}
    #pickler2.memo = unpickler2.memo = {}

    d = {}

    pickler1.dump(d)
    f1.seek(0)
    d_other = unpickler2.load()

    # translate unpickler2 memo to pickler2
    pickler2.memo = dict([(id(obj), (int(x), obj))
                            for x, obj in unpickler2.memo.items()])

    pickler2.dump(d_other)
    f2.seek(0)

    unpickler1.memo = dict([(str(x), y) for x, y in pickler1.memo.values()])

    d_back = unpickler1.load()

    assert d is d_back

def test_cpickle():
    import cPickle
    pickletest(cPickle)

def test_pickle():
    import pickle
    pickletest(pickle)

