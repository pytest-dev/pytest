import os, random
from pygreen.pipelayer import PipeLayer, pipe_over_udp, PipeOverUdp
import py

def test_simple():
    data1 = os.urandom(1000)
    data2 = os.urandom(1000)
    p1 = PipeLayer()
    p2 = PipeLayer()
    p2._dump_indent = 40
    p1.queue(data1)
    p1.queue(data2)
    recv = ''
    while len(recv) < 2000:
        raw = p1.encode(64)
        assert raw is not None
        res = p2.decode(raw)
        assert res is not None
        recv += res
    assert recv == data1 + data2
    raw = p1.encode(64)
    assert raw is None

def test_stabilize():
    data1 = os.urandom(28)
    p1 = PipeLayer()
    p2 = PipeLayer()
    p2._dump_indent = 40
    p1.queue(data1)
    recv = ''
    t = 0.0
    print
    while True:
        delay1 = p1.settime(t)
        delay2 = p2.settime(t)
        t += 0.100000001
        if delay1 is delay2 is None:
            break
        if delay1 == 0:
            raw = p1.encode(10)
            p1.dump('OUT', raw)
            assert raw is not None
            res = p2.decode(raw)
            assert res is not None
            recv += res
        if delay2 == 0:
            raw = p2.encode(10)
            p2.dump('OUT', raw)
            assert raw is not None
            res = p1.decode(raw)
            assert res == ''
    assert recv == data1

def test_bidir():
    data1 = os.urandom(1000)
    data2 = os.urandom(1000)
    p1 = PipeLayer()
    p2 = PipeLayer()
    p2._dump_indent = 40
    p1.queue(data1)
    p2.queue(data2)
    recv = ['', '']
    while len(recv[0]) < 1000 or len(recv[1]) < 1000:
        progress = False
        for (me, other, i) in [(p1, p2, 1), (p2, p1, 0)]:
            raw = me.encode(64)
            if raw is not None:
                res = other.decode(raw)
                assert res is not None
                recv[i] += res
                if res:
                    progress = True
        assert progress
    assert recv[0] == data2
    assert recv[1] == data1
    raw = p1.encode(64)
    assert raw is None
    raw = p2.encode(64)
    assert raw is None

def test_with_loss():
    data1 = os.urandom(10000).encode('hex')
    data2 = os.urandom(10000).encode('hex')
    #data1 = '0123456789'
    #data2 = 'ABCDEFGHIJ'
    p1 = PipeLayer()
    p2 = PipeLayer()
    p2._dump_indent = 40
    p1.queue(data1)
    p2.queue(data2)
    recv = ['', '']
    time = 0
    active = 1
    while active:
        active = 0
        time += 0.2
        #print '.'
        exchange = []
        for (me, other, i) in [(p1, p2, 1), (p2, p1, 0)]:
            to = me.settime(time)
            packet = me.encode(12)
            assert (packet is not None) == (to == 0)
            if to is not None:
                active = 1
                if to == 0:
                    exchange.append((packet, other, i))
        for (packet, other, i) in exchange:
            if random.random() < 0.5:
                pass   # drop packet
            else:
                res = other.decode(packet)
                assert res is not None
                recv[i] += res
        assert data2.startswith(recv[0])
        assert data1.startswith(recv[1])
    assert recv[0] == data2
    assert recv[1] == data1
    print time

def test_massive_reordering():
    data1 = os.urandom(10000).encode('hex')
    data2 = os.urandom(10000).encode('hex')
    #data1 = '0123456789'
    #data2 = 'ABCDEFGHIJ'
    p1 = PipeLayer()
    p2 = PipeLayer()
    p2._dump_indent = 40
    p1.queue(data1)
    p2.queue(data2)
    recv = ['', '']
    time = 0
    active = 1
    exchange = []
    while active or exchange:
        active = 0
        time += 0.2
        #print '.'
        for (me, other, i) in [(p1, p2, 1), (p2, p1, 0)]:
            to = me.settime(time)
            packet = me.encode(12)
            assert (packet is not None) == (to == 0)
            if to is not None:
                active = 1
                if to == 0:
                    exchange.append((packet, other, i))
        if random.random() < 0.02:
            random.shuffle(exchange)
            for (packet, other, i) in exchange:
                res = other.decode(packet)
                assert res is not None
                recv[i] += res
            exchange = []
        assert data2.startswith(recv[0])
        assert data1.startswith(recv[1])
    assert recv[0] == data2
    assert recv[1] == data1
    print time

def udpsockpair():
    from socket import socket, AF_INET, SOCK_DGRAM, INADDR_ANY
    s1 = socket(AF_INET, SOCK_DGRAM)
    s2 = socket(AF_INET, SOCK_DGRAM)
    s1.bind(('127.0.0.1', INADDR_ANY))
    s2.bind(('127.0.0.1', INADDR_ANY))
    s2.connect(s1.getsockname())
    s1.connect(s2.getsockname())
    return s1, s2

def test_pipe_over_udp():
    import thread
    s1, s2 = udpsockpair()

    tmp = py.test.ensuretemp("pipeoverudp")
    p = py.path.local(__file__)
    p.copy(tmp.join(p.basename))
    old = tmp.chdir()
    try:
        fd1 = os.open(__file__, os.O_RDONLY)
        fd2 = os.open('test_pipelayer.py~copy', os.O_WRONLY|os.O_CREAT|os.O_TRUNC)

        thread.start_new_thread(pipe_over_udp, (s1, fd1))
        pipe_over_udp(s2, recv_fd=fd2, inactivity_timeout=2.5)
        os.close(fd1)
        os.close(fd2)
        f = open(__file__, 'rb')
        data1 = f.read()
        f.close()
        f = open('test_pipelayer.py~copy', 'rb')
        data2 = f.read()
        f.close()
        assert data1 == data2
        os.unlink('test_pipelayer.py~copy')
    finally:
        old.chdir()

def test_PipeOverUdp():
    s1, s2 = udpsockpair()
    p1 = PipeOverUdp(s1, timeout=0.2)
    p2 = PipeOverUdp(s2, timeout=0.2)
    p2.sendall('goodbye')
    for k in range(10):
        p1.sendall('hello world')
        input = p2.recvall(11)
        assert input == 'hello world'
    input = p1.recvall(7)
    assert input == 'goodbye'

    bigchunk1 = os.urandom(500000)
    bigchunk2 = os.urandom(500000)
    i1 = i2 = 0
    j1 = j2 = 0
    while j1 < len(bigchunk1) or j2 < len(bigchunk2):
        i1 += p1.send(bigchunk1[i1:i1+512])
        i2 += p2.send(bigchunk2[i2:i2+512])
        data = p1.recv(512)
        assert data == bigchunk2[j2:j2+len(data)]
        j2 += len(data)
        data = p2.recv(512)
        assert data == bigchunk1[j1:j1+len(data)]
        j1 += len(data)
        #print i1, i2, j1, j2
    p1.close()
    p2.close()
