
import py
from py.__.test.dist.mypickle import ImmutablePickler, PickleChannel, UnpickleError

class A: 
    pass
def test_pickle_and_back_IS_same():
    def pickle_band_back_IS_same(obj, proto):
        p1 = ImmutablePickler(uneven=False, protocol=proto)
        p2 = ImmutablePickler(uneven=True, protocol=proto)
        s1 = p1.dumps(obj)
        d2 = p2.loads(s1)
        s2 = p2.dumps(d2)
        obj_back = p1.loads(s2)
        assert obj is obj_back 

    a1 = A()
    a2 = A()
    a2.a1 = a1
    for proto in (0,1,2, -1):
        for obj in {1:2}, [1,2,3], a1, a2:
            yield pickle_band_back_IS_same, obj, proto

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
        cls.gw = py.execnet.PopenGateway()
        cls.gw.remote_init_threads(5)

    def teardown_class(cls):
        cls.gw.exit()

    def test_popen_send_instance(self):
        channel = self.gw.remote_exec("""
            from py.__.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from py.__.test.dist.testing.test_mypickle import A
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
            from py.__.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from py.__.test.dist.testing.test_mypickle import A
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
            from py.__.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from py.__.test.dist.testing.test_mypickle import A
            a1 = A()
            a1.hello = 10
            channel.send(a1)
            a2 = channel.receive()
            channel.send(a2 is a1)
        """)
        channel = PickleChannel(channel)
        queue = py.std.Queue.Queue()
        channel.setcallback(queue.put)
        a_received = queue.get(timeout=TESTTIMEOUT)
        assert isinstance(a_received, A)
        assert a_received.hello == 10
        channel.send(a_received)
        #remote_a2_is_a1 = queue.get(timeout=TESTTIMEOUT)
        #assert remote_a2_is_a1 

    def test_popen_with_callback_with_endmarker(self):
        channel = self.gw.remote_exec("""
            from py.__.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from py.__.test.dist.testing.test_mypickle import A
            a1 = A()
            a1.hello = 10
            channel.send(a1)
            a2 = channel.receive()
            channel.send(a2 is a1)
        """)
        channel = PickleChannel(channel)
        queue = py.std.Queue.Queue()
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
            from py.__.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from py.__.test.dist.testing.test_mypickle import A
            a1 = A()
            channel.send(a1)
            channel.send(a1)
        """)
        channel = PickleChannel(channel)
        queue = py.std.Queue.Queue()
        a = channel.receive()
        channel._ipickle._unpicklememo.clear()
        channel.setcallback(queue.put, endmarker=-1)
        next = queue.get(timeout=TESTTIMEOUT)
        assert next == -1 
        error = channel._getremoteerror()
        assert isinstance(error, UnpickleError)

    def test_popen_with_newchannel(self):
        channel = self.gw.remote_exec("""
            from py.__.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            newchannel = channel.receive()
            newchannel.send(42)
        """)
        channel = PickleChannel(channel)
        newchannel = self.gw.newchannel()
        channel.send(newchannel)
        channel.waitclose()
        res = newchannel.receive()
        assert res == 42

    def test_popen_with_various_methods(self):
        channel = self.gw.remote_exec("""
            from py.__.test.dist.mypickle import PickleChannel
            channel = PickleChannel(channel)
            channel.receive()
        """)
        channel = PickleChannel(channel)
        assert not channel.isclosed()
        assert not channel._getremoteerror()
        channel.send(2)
        channel.waitclose(timeout=2)

