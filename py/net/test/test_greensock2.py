import py
from socket import *
from py.__.net.greensock2 import *

def test_meetingpoint():
    giv1, acc1 = meetingpoint()
    giv2, acc2 = meetingpoint()
    giv3, acc3 = meetingpoint()

    lst = []

    def g1():
        lst.append(0)
        x = acc2.accept()
        assert x == 'hello'
        lst.append(2)
        giv1.give('world')
        lst.append(5)
        x = acc3.accept()
        assert x == 'middle'
        lst.append(6)
        giv3.give('done')

    def g2():
        lst.append(1)
        giv2.give('hello')
        lst.append(3)
        y = acc1.accept()
        assert y == 'world'
        lst.append(4)

    autogreenlet(g1)
    autogreenlet(g2)
    giv3.give('middle')
    tag = acc3.accept()
    assert tag == 'done'
    assert lst == [0, 1, 2, 3, 4, 5, 6]


def test_producer():
    lst = []

    def prod(n):
        lst.append(1)
        yield n
        lst.append(2)
        yield 87
        lst.append(3)

    def cons():
        lst.append(4)
        accepter = producer(prod, 145)
        lst.append(5)
        lst.append(accepter.accept())
        lst.append(6)
        lst.append(accepter.accept())
        lst.append(7)
        try:
            accepter.accept()
        except Interrupted:
            lst.append(8)

    oneof(cons)
    assert lst == [4, 5, 1, 145, 6, 2, 87, 7, 3, 8]


def test_timer():
    lst = []

    def g1():
        sleep(0.1)
        lst.append(1)
        sleep(0.2)
        lst.append(3)

    def g2():
        lst.append(0)
        sleep(0.2)
        lst.append(2)
        sleep(0.2)
        lst.append(4)

    oneof(g1, g2)
    assert lst == [0, 1, 2, 3]

def test_kill_other():

    def g1():
        sleep(.1)
        return 1

    def g2():
        sleep(.2)
        return 2

    res = oneof(g1, g2)
    assert res == 1

def test_socket():
    s1 = socket(AF_INET, SOCK_DGRAM)
    s2 = socket(AF_INET, SOCK_DGRAM)
    s1.bind(('', INADDR_ANY))
    s2.bind(('', INADDR_ANY))
    s1.connect(s2.getsockname())
    s2.connect(s1.getsockname())

    lst = []

    def g1():
        lst.append(0)
        x = recv(s1, 5)
        assert x == 'hello'
        lst.append(3)
        sendall(s1, 'world')
        lst.append(4)
        return 1

    def g2():
        lst.append(1)
        sendall(s2, 'hello')
        lst.append(2)
        y = recv(s2, 5)
        assert y == 'world'
        lst.append(5)
        return 2

    one, two = allof(g1, g2)
    assert lst == [0, 1, 2, 3, 4, 5]
    assert one == 1
    assert two == 2

##def test_Queue():

##    def g1():
##        lst.append(5)
##        q.put(6)
##        lst.append(7)
##        q.put(8)
##        lst.append(9)
##        q.put(10)
##        lst.append(11)
##        q.put(12)    # not used

##    def g2():
##        lst.append(1)
##        lst.append(q.get())
##        lst.append(2)
##        lst.append(q.get())
##        lst.append(3)
##        lst.append(q.get())
##        lst.append(4)

##    q = Queue()
##    lst = []
##    autogreenlet(g1)
##    autogreenlet(g2)
##    wait()
##    assert lst == [5, 7, 9, 11, 1, 6, 2, 8, 3, 10, 4]

##    q = Queue()
##    lst = []
##    autogreenlet(g2)
##    autogreenlet(g1)
##    wait()
##    assert lst == [1, 5, 7, 9, 11, 6, 2, 8, 3, 10, 4]


##def test_Event():

##    def g1():
##        assert not e.isSet()
##        e.wait()
##        assert not e.isSet()   # no longer set
##        lst.append(1)
##        e.set()
##        e.wait()
##        lst.append(2)
##        assert e.isSet()
##        e.clear()
##        assert not e.isSet()
##        lst.append(0)
##        e.set()
##        lst.append(3)
##        assert e.isSet()

##    def g2():
##        assert not e.isSet()
##        lst.append(4)
##        e.set()
##        lst.append(7)
##        e.clear()
##        e.set()
##        e.clear()
##        assert not e.isSet()
##        lst.append(5)
##        e.wait()
##        assert e.isSet()
##        lst.append(6)

##    e = Event()
##    lst = []
##    autogreenlet(g1)
##    autogreenlet(g2)
##    wait()
##    assert lst == [4, 7, 5, 1, 2, 0, 3, 6]


##def test_Event_timeout():
##    def g1():
##        lst.append(5)
##        e.wait(0.1)
##        lst.append(e.isSet())
##        e.wait(60.0)
##        lst.append(e.isSet())
##    lst = []
##    e = Event()
##    autogreenlet(g1)
##    sleep(0.5)
##    e.set()
##    wait()
##    assert lst == [5, False, True]
