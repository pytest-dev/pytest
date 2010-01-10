
import py
import sys
import execnet

Queue = py.builtin._tryimport('queue', 'Queue').Queue

from py.impl.test.dist.mypickle import ImmutablePickler, PickleChannel
from py.impl.test.dist.mypickle import UnpickleError, makekey
# first let's test some basic functionality 

def pytest_generate_tests(metafunc):
    if 'picklemod' in metafunc.funcargnames:
        import pickle
        metafunc.addcall(funcargs={'picklemod': pickle})
        try:
            import cPickle
        except ImportError:
            pass
        else:
            metafunc.addcall(funcargs={'picklemod': cPickle})
    elif "obj" in metafunc.funcargnames and "proto" in metafunc.funcargnames:
        a1 = A()
        a2 = A()
        a2.a1 = a1
        for proto in (0,1,2, -1):
            for obj in {1:2}, [1,2,3], a1, a2:
                metafunc.addcall(funcargs=dict(obj=obj, proto=proto))

def test_underlying_basic_pickling_mechanisms(picklemod):
    f1 = py.io.BytesIO()
    f2 = py.io.BytesIO()

    pickler1 = picklemod.Pickler(f1)
    unpickler1 = picklemod.Unpickler(f2)

    pickler2 = picklemod.Pickler(f2)
    unpickler2 = picklemod.Unpickler(f1)

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
        
    unpickler1.memo = dict([(makekey(x), y) 
                                for x, y in pickler1.memo.values()])
    d_back = unpickler1.load()
    assert d is d_back


class A: 
    pass

        
def test_pickle_and_back_IS_same(obj, proto):
    p1 = ImmutablePickler(uneven=False, protocol=proto)
    p2 = ImmutablePickler(uneven=True, protocol=proto)
    s1 = p1.dumps(obj)
    d2 = p2.loads(s1)
    s2 = p2.dumps(d2)
    obj_back = p1.loads(s2)
    assert obj is obj_back 

def test_pickling_twice_before_unpickling():
    p1 = ImmutablePickler(uneven=False)
    p2 = ImmutablePickler(uneven=True)

    a1 = A()
    a2 = A()
    a3 = A() 
    a3.a1 = a1
    a2.a1 = a1
    s1 = p1.dumps(a1)
    a1.a3 = a3
    s2 = p1.dumps(a2)
    other_a1 = p2.loads(s1)
    other_a2 = p2.loads(s2)
    back_a1 = p1.loads(p2.dumps(other_a1))
    other_a3 = p2.loads(p1.dumps(a3))
    back_a3 = p1.loads(p2.dumps(other_a3))
    back_a2 = p1.loads(p2.dumps(other_a2))
    back_a1 = p1.loads(p2.dumps(other_a1))
    assert back_a1 is a1
    assert back_a2 is a2

def test_pickling_concurrently():
    p1 = ImmutablePickler(uneven=False)
    p2 = ImmutablePickler(uneven=True)

    a1 = A()
    a1.hasattr = 42
    a2 = A()

    s1 = p1.dumps(a1)  
    s2 = p2.dumps(a2)
    other_a1 = p2.loads(s1)
    other_a2 = p1.loads(s2)
    a1_back = p1.loads(p2.dumps(other_a1))

def test_self_memoize():
    p1 = ImmutablePickler(uneven=False)
    a1 = A()
    p1.selfmemoize(a1)
    x = p1.loads(p1.dumps(a1))
    assert x is a1

TESTTIMEOUT = 2.0
class TestPickleChannelFunctional:
    def setup_class(cls):
        cls.gw = execnet.PopenGateway()
        cls.gw.remote_exec(
            "import py ; py.path.local(%r).pyimport()" %(__file__)
        )
        cls.gw.remote_init_threads(5)
        # we need the remote test code to import 
        # the same test module here

    def test_popen_send_instance(self):
        channel = self.gw.remote_exec("""
            from py.impl.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from testing.pytest.dist.test_mypickle import A
            a1 = A()
            a1.hello = 10
            channel.send(a1)
            a2 = channel.receive()
            channel.send(a2 is a1)
        """)
        channel = PickleChannel(channel)
        a_received = channel.receive()
        assert isinstance(a_received, A)
        assert a_received.hello == 10
        channel.send(a_received)
        remote_a2_is_a1 = channel.receive()
        assert remote_a2_is_a1 

    def test_send_concurrent(self):
        channel = self.gw.remote_exec("""
            from py.impl.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from testing.pytest.dist.test_mypickle import A
            l = [A() for i in range(10)]
            channel.send(l)
            other_l = channel.receive() 
            channel.send((l, other_l))
            channel.send(channel.receive())
            channel.receive()
        """)
        channel = PickleChannel(channel)
        l = [A() for i in range(10)]
        channel.send(l)
        other_l = channel.receive()
        channel.send(other_l)
        ret = channel.receive()
        assert ret[0] is other_l
        assert ret[1] is l 
        back = channel.receive()
        assert other_l is other_l 
        channel.send(None)

    #s1 = p1.dumps(a1)  
    #s2 = p2.dumps(a2)
    #other_a1 = p2.loads(s1)
    #other_a2 = p1.loads(s2)
    #a1_back = p1.loads(p2.dumps(other_a1))
        
    def test_popen_with_callback(self):
        channel = self.gw.remote_exec("""
            from py.impl.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from testing.pytest.dist.test_mypickle import A
            a1 = A()
            a1.hello = 10
            channel.send(a1)
            a2 = channel.receive()
            channel.send(a2 is a1)
        """)
        channel = PickleChannel(channel)
        queue = Queue()
        channel.setcallback(queue.put)
        a_received = queue.get(timeout=TESTTIMEOUT)
        assert isinstance(a_received, A)
        assert a_received.hello == 10
        channel.send(a_received)
        #remote_a2_is_a1 = queue.get(timeout=TESTTIMEOUT)
        #assert remote_a2_is_a1 

    def test_popen_with_callback_with_endmarker(self):
        channel = self.gw.remote_exec("""
            from py.impl.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from testing.pytest.dist.test_mypickle import A
            a1 = A()
            a1.hello = 10
            channel.send(a1)
            a2 = channel.receive()
            channel.send(a2 is a1)
        """)
        channel = PickleChannel(channel)
        queue = Queue()
        channel.setcallback(queue.put, endmarker=-1)
          
        a_received = queue.get(timeout=TESTTIMEOUT)
        assert isinstance(a_received, A)
        assert a_received.hello == 10
        channel.send(a_received)
        remote_a2_is_a1 = queue.get(timeout=TESTTIMEOUT)
        assert remote_a2_is_a1 
        endmarker = queue.get(timeout=TESTTIMEOUT)
        assert endmarker == -1

    def test_popen_with_callback_with_endmarker_and_unpickling_error(self):
        channel = self.gw.remote_exec("""
            from py.impl.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from testing.pytest.dist.test_mypickle import A
            a1 = A()
            channel.send(a1)
            channel.send(a1)
        """)
        channel = PickleChannel(channel)
        queue = Queue()
        a = channel.receive()
        channel._ipickle._unpicklememo.clear()
        channel.setcallback(queue.put, endmarker=-1)
        next = queue.get(timeout=TESTTIMEOUT)
        assert next == -1 
        error = channel._getremoteerror()
        assert isinstance(error, UnpickleError)

    def test_popen_with_various_methods(self):
        channel = self.gw.remote_exec("""
            from py.impl.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            channel.receive()
        """)
        channel = PickleChannel(channel)
        assert not channel.isclosed()
        assert not channel._getremoteerror()
        channel.send(2)
        channel.waitclose(timeout=2)


