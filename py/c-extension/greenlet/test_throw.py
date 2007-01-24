import py
try:
    from py.magic import greenlet
except (ImportError, RuntimeError), e:
    py.test.skip(str(e))

def switch(*args):
    return greenlet.getcurrent().parent.switch(*args)

def test_class():
    def f():
        try:
            switch("ok")
        except RuntimeError:
            switch("ok")
            return
        switch("fail")

    g = greenlet(f)
    res = g.switch()
    assert res == "ok"
    res = g.throw(RuntimeError)
    assert res == "ok"

def test_val():
    def f():
        try:
            switch("ok")
        except RuntimeError, val:
            if str(val) == "ciao":
                switch("ok")
                return
        switch("fail")

    g = greenlet(f)
    res = g.switch()
    assert res == "ok"
    res = g.throw(RuntimeError("ciao"))
    assert res == "ok"

    g = greenlet(f)
    res = g.switch()
    assert res == "ok"
    res = g.throw(RuntimeError, "ciao")
    assert res == "ok"

def test_kill():
    def f():
        switch("ok")
        switch("fail")

    g = greenlet(f)
    res = g.switch()
    assert res == "ok"
    res = g.throw()
    assert isinstance(res, greenlet.GreenletExit)
    assert g.dead
    res = g.throw()    # immediately eaten by the already-dead greenlet
    assert isinstance(res, greenlet.GreenletExit)

def test_throw_goes_to_original_parent():
    main = greenlet.getcurrent()
    def f1():
        try:
            main.switch("f1 ready to catch")
        except IndexError:
            return "caught"
        else:
            return "normal exit"
    def f2():
        main.switch("from f2")

    g1 = greenlet(f1)
    g2 = greenlet(f2, parent=g1)
    py.test.raises(IndexError, g2.throw, IndexError)
    assert g2.dead
    assert g1.dead

    g1 = greenlet(f1)
    g2 = greenlet(f2, parent=g1)
    res = g1.switch()
    assert res == "f1 ready to catch"
    res = g2.throw(IndexError)
    assert res == "caught"
    assert g2.dead
    assert g1.dead

    g1 = greenlet(f1)
    g2 = greenlet(f2, parent=g1)
    res = g1.switch()
    assert res == "f1 ready to catch"
    res = g2.switch()
    assert res == "from f2"
    res = g2.throw(IndexError)
    assert res == "caught"
    assert g2.dead
    assert g1.dead
