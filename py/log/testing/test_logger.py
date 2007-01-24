
import py

def test_logger_identity():
    assert py.log.get() is py.log.get() 
    otherkey = object()
    for key in "name1", object():
        log = py.log.get(key)
        assert py.log.get(key) is log 
        assert py.log.get(otherkey) is not log 

def test_log_preset():
    log = py.log.get(test_log_preset) 
    l2 = []
    log.set_sub(x1=None, x2=l2.append)
    l3 = []
    log2 = py.log.get(test_log_preset, 
                      x2=None,
                      x3=l3.append)

    log2.x2("hello")
    log2.x3("world")
    assert l2[0].strcontent() == "hello"
    assert l3[0].strcontent() == "world"

def test_log_override():
    l2 = []
    log = py.log.get(object(), x1=None, x2=l2.append)
    l = []
    log.set_override(l.append)
    log.x1("hello")
    log.x2("world")
    log.ensure_sub(x3=None)
    log.x3(42)
    assert len(l) == 3
    assert not l2
    r = [x.strcontent() for x in l]
    assert r == ["hello", "world", "42"]
    l[:] = []
    log.del_override()
    log.del_override()
    log.x2("hello")
    assert l2[0].strcontent() == "hello"

def test_log_basic():
    l1 = []
    class SomeKey:
        def __str__(self):
            return "somekey"

    for key in "name1", SomeKey(): 
        log = py.log.get(key)
        log.set_sub(x1=l1.append) 
        log.x1(42)
        assert l1[-1].content == (42,)
        assert l1[-1].strcontent() == "42"
        assert l1[-1].keywords == (key, 'x1')
        assert l1[-1].strprefix() == "[%s:x1] " %(key,)

        #log.set_prefix("hello")
        #assert l1[0].strprefix() == "hello"
        #log("world")
        #assert str(l1[-1]) == "hello world" 

class TestLogger:
    def setup_method(self, method):
        self._x1 = []
        self._x2 = []
        self.log = py.log.get()
        self.log.set_sub(x1=self._x1.append, 
                         x2=self._x2.append) 
    
    #def teardown_method(self, method):
    #    self.log.close() 

    def test_simple(self):
        self.log.x1("hello")
        self.log.x2("world")
        assert self._x1[0].strcontent() == 'hello'
        assert self._x1[0].strprefix() == '[global:x1] '
        assert self._x2[0].strcontent() == 'world'
        assert self._x2[0].strprefix() == '[global:x2] '
        py.test.raises(AttributeError, "self.log.x3")

    def test_reconfig(self):
        self.log.set_sub(x1=None)
        self.log.x1("asdasd")
        assert not self._x1

    def test_reconfig_add(self):
        l = []
        self.log.set_sub(x2=None, x3=l.append) 
        self.log.x2("asdhello")
        assert not self._x2
        self.log.x3(123) 
        assert l[0].content == (123,)

    def test_logger_del(self):
        del self.log.x2 
        py.test.raises(AttributeError, "self.log.x2")

