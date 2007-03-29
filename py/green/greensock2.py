
""" This is a base implementation of thread-like network programming
on top of greenlets. From API available here it's quite unlikely
that you would like to use anything except wait(). Higher level interface
is available in pipe directory
"""

import os, sys
try:
    from stackless import greenlet
except ImportError:
    import py
    greenlet = py.magic.greenlet
from collections import deque
from select import select as _select
from time import time as _time
from heapq import heappush, heappop, heapify

TRACE = False

def meetingpoint():
    senders = deque()    # list of senders, or [None] if Giver closed
    receivers = deque()  # list of receivers, or [None] if Receiver closed
    return (MeetingPointGiver(senders, receivers),
            MeetingPointAccepter(senders, receivers))

def producer(func, *args, **kwds):
    iterable = func(*args, **kwds)
    giver, accepter = meetingpoint()
    def autoproducer():
        try:
            giver.wait()
            for obj in iterable:
                giver.give(obj)
                giver.wait()
        finally:
            giver.close()
    autogreenlet(autoproducer)
    return accepter


class MeetingPointBase(object):

    def __init__(self, senders, receivers):
        self.senders = senders
        self.receivers = receivers
        self.g_active = g_active

    def close(self):
        while self.senders:
            if self.senders[0] is None:
                break
            packet = self.senders.popleft()
            if packet.g_from is not None:
                self.g_active.append(packet.g_from)
        else:
            self.senders.append(None)
        while self.receivers:
            if self.receivers[0] is None:
                break
            other = self.receivers.popleft()
            self.g_active.append(other)
        else:
            self.receivers.append(None)

    __del__ = close

    def closed(self):
        return self.receivers and self.receivers[0] is None


class MeetingPointGiver(MeetingPointBase):

    def give(self, obj):
        if self.receivers:
            if self.receivers[0] is None:
                raise MeetingPointClosed
            other = self.receivers.popleft()
            g_active.append(g_getcurrent())
            packet = _Packet()
            packet.payload = obj
            other.switch(packet)
            if not packet.accepted:
                raise Interrupted("packet not accepted")
        else:
            packet = _Packet()
            packet.g_from = g_getcurrent()
            packet.payload = obj
            try:
                self.senders.append(packet)
                g_dispatcher.switch()
                if not packet.accepted:
                    raise Interrupted("packet not accepted")
            except:
                remove_by_id(self.senders, packet)
                raise

    def give_queued(self, obj):
        if self.receivers:
            self.give(obj)
        else:
            packet = _Packet()
            packet.g_from = None
            packet.payload = obj
            self.senders.append(packet)

    def ready(self):
        return self.receivers and self.receivers[0] is not None

    def wait(self):
        if self.receivers:
            if self.receivers[0] is None:
                raise MeetingPointClosed
        else:
            packet = _Packet()
            packet.g_from = g_getcurrent()
            packet.empty = True
            self.senders.append(packet)
            try:
                g_dispatcher.switch()
                if not packet.accepted:
                    raise Interrupted("no accepter found")
            except:
                remove_by_id(self.senders, packet)
                raise

    def trigger(self):
        if self.ready():
            self.give(None)


class MeetingPointAccepter(MeetingPointBase):

    def accept(self):
        while self.senders:
            if self.senders[0] is None:
                raise MeetingPointClosed
            packet = self.senders.popleft()
            packet.accepted = True
            if packet.g_from is not None:
                g_active.append(packet.g_from)
            if not packet.empty:
                return packet.payload
        g = g_getcurrent()
        self.receivers.append(g)
        try:
            packet = g_dispatcher.switch()
        except:
            remove_by_id(self.receivers, g)
            raise
        if type(packet) is not _Packet:
            remove_by_id(self.receivers, g)
            raise Interrupted("no packet")
        packet.accepted = True
        return packet.payload

    def ready(self):
        for packet in self.senders:
            if packet is None:
                return False
            if not packet.empty:
                return True
        return False

    def wait_trigger(self, timeout=None, default=None):
        if timeout is None:
            return self.accept()
        else:
            timer = Timer(timeout)
            try:
                try:
                    return self.accept()
                finally:
                    timer.stop()
            except Interrupted:
                if timer.finished:
                    return default
                raise


class MeetingPointClosed(greenlet.GreenletExit):
    pass

class Interrupted(greenlet.GreenletExit):
    pass

class ConnexionClosed(greenlet.GreenletExit):
    pass

class _Packet(object):
    empty = False
    accepted = False

def remove_by_id(d, obj):
    lst = [x for x in d if x is not obj]
    d.clear()
    d.extend(lst)

def wait_input(sock):
    _register(g_iwtd, sock)

def recv(sock, bufsize):
    wait_input(sock)
    buf = sock.recv(bufsize)
    if not buf:
        raise ConnexionClosed("inbound connexion closed")
    return buf

def recvall(sock, bufsize):
    in_front = False
    data = []
    while bufsize > 0:
        _register(g_iwtd, sock, in_front=in_front)
        buf = sock.recv(bufsize)
        if not buf:
            raise ConnexionClosed("inbound connexion closed")
        data.append(buf)
        bufsize -= len(buf)
        in_front = True
    return ''.join(data)

def read(fd, bufsize):
    assert fd >= 0
    wait_input(fd)
    buf = os.read(fd, bufsize)
    if not buf:
        raise ConnexionClosed("inbound connexion closed")
    return buf

def readall(fd, bufsize):
    assert fd >= 0
    in_front = False
    data = []
    while bufsize > 0:
        _register(g_iwtd, fd, in_front=in_front)
        buf = os.read(fd, bufsize)
        if not buf:
            raise ConnexionClosed("inbound connexion closed")
        data.append(buf)
        bufsize -= len(buf)
        in_front = True
    return ''.join(data)


def wait_output(sock):
    _register(g_owtd, sock)

def sendall(sock, buffer):
    in_front = False
    while buffer:
        _register(g_owtd, sock, in_front=in_front)
        count = sock.send(buffer)
        buffer = buffer[count:]
        in_front = True

def writeall(fd, buffer):
    assert fd >= 0
    in_front = False
    while buffer:
        _register(g_owtd, fd, in_front=in_front)
        count = os.write(fd, buffer)
        if not count:
            raise ConnexionClosed("outbound connexion closed")
        buffer = buffer[count:]
        in_front = True


def sleep(duration):
    timer = Timer(duration)
    try:
        _suspend_forever()
    finally:
        ok = timer.finished
        timer.stop()
    if not ok:
        raise Interrupted

def _suspend_forever():
    g_dispatcher.switch()

def oneof(*callables):
    assert callables
    for c in callables:
        assert callable(c)
    greenlets = [tracinggreenlet(c) for c in callables]
    g_active.extend(greenlets)
    res = g_dispatcher.switch()
    for g in greenlets:
        g.interrupt()
    return res

def allof(*callables):
    for c in callables:
        assert callable(c)
    greenlets = [tracinggreenlet(lambda i=i, c=c: (i, c()))
                 for i, c in enumerate(callables)]
    g_active.extend(greenlets)
    result = [None] * len(callables)
    for _ in callables:
        num, res = g_dispatcher.switch()
        result[num] = res
    return tuple(result)

class Timer(object):
    started = False
    finished = False

    def __init__(self, timeout):
        self.g = g_getcurrent()
        entry = (_time() + timeout, self)
        if g_timers_mixed:
            g_timers.append(entry)
        else:
            heappush(g_timers, entry)

    def stop(self):
        global g_timers_mixed
        if not self.finished:
            for i, (activationtime, timer) in enumerate(g_timers):
                if timer is self:
                    g_timers[i] = g_timers[-1]
                    g_timers.pop()
                    g_timers_mixed = True
                    break
            self.finished = True

# ____________________________________________________________

class tracinggreenlet(greenlet):
    def __init__(self, function, *args, **kwds):
        self.function = function
        self.args = args
        self.kwds = kwds

    def __repr__(self):
##        args = ', '.join([repr(s) for s in self.args] +
##                        ['%s=%r' % keyvalue for keyvalue in self.kwds.items()])
##        return '<autogreenlet %s(%s)>' % (self.function.__name__, args)
        return '<%s %s at %s>' % (self.__class__.__name__,
                                  self.function.__name__,
                                  hex(id(self)))

    def run(self):
        self.trace("start")
        try:
            res = self.function(*self.args, **self.kwds)
        except Exception, e:
            self.trace("stop (%s%s)", e.__class__.__name__,
                       str(e) and (': '+str(e)))
            raise
        else:
            self.trace("done")
            return res

    def trace(self, msg, *args):
        if TRACE:
            print self, msg % args

    def interrupt(self):
        self.throw(Interrupted)

class autogreenlet(tracinggreenlet):
    def __init__(self, *args, **kwargs):
        super(autogreenlet, self).__init__(*args, **kwargs)
        self.parent = g_dispatcher
        g_active.append(self)

g_active = deque()
g_iwtd = {}
g_owtd = {}
g_timers = []
g_timers_mixed = False

g_getcurrent = greenlet.getcurrent

def _register(g_wtd, sock, in_front=False):
    d = g_wtd.setdefault(sock, deque())
    g = g_getcurrent()
    if in_front:
        d.appendleft(g)
    else:
        d.append(g)
    try:
        if g_dispatcher.switch() is not g_wtd:
            raise Interrupted
    except:
        remove_by_id(d, g) 
        raise

##def _unregister_timer():
##    ...


def check_dead_greenlets(mapping):
    to_remove = [i for i, v in mapping.items() if not v]
    for k in to_remove:
        del mapping[k]

#def check_waiters(active):
#    if active in g_waiters:
#        for g in g_waiters[active]:
#            g.switch()
#        del g_waiters[active]


def dispatcher_mainloop():
    global g_timers_mixed
    GreenletExit = greenlet.GreenletExit
    while 1:
        try:
            while g_active:
                #print 'active:', g_active[0]
                g_active.popleft().switch()
#                active.switch()
#                if active.dead:
#                    check_waiters(active)
#                    del active
            if g_timers:
                if g_timers_mixed:
                    heapify(g_timers)
                    g_timers_mixed = False
                activationtime, timer = g_timers[0]
                delay = activationtime - _time()
                if delay <= 0.0:
                    if timer.started:
                        heappop(g_timers)
                        #print 'timeout:', g
                        timer.finished = True
                        timer.g.switch()
#                        if timer.g.dead:
#                            check_waiters(timer.g)
                        continue
                    delay = 0.0
                timer.started = True
            else:
                check_dead_greenlets(g_iwtd)
                check_dead_greenlets(g_owtd)
                if not (g_iwtd or g_owtd):
                    # nothing to do, switch to the main greenlet
                    g_dispatcher.parent.switch()
                    continue
                delay = None

            #print 'selecting...', g_iwtd.keys(), g_owtd.keys(), delay
            iwtd, owtd, _ = _select(g_iwtd.keys(), g_owtd.keys(), [], delay)
            #print 'done'
            for s in owtd:
                if s in g_owtd:
                    d = g_owtd[s]
                    #print 'owtd:', d[0]
                    # XXX: Check if d is non-empty
                    try:
                        g = d.popleft()
                    except IndexError:
                        g = None
                    if not d:
                        try:
                            del g_owtd[s]
                        except KeyError:
                            pass
                    if g:
                        g.switch(g_owtd)
#                    if g.dead:
#                        check_waiters(g)
            for s in iwtd:
                if s in g_iwtd:
                    d = g_iwtd[s]
                    #print 'iwtd:', d[0]
                    # XXX: Check if d is non-empty
                    try:
                        g = d.popleft()
                    except IndexError:
                        g = None
                    if not d:
                        try:
                            del g_iwtd[s]
                        except KeyError:
                            pass
                    if g:
                        g.switch(g_iwtd)
#                    if g.dead:
#                        check_waiters(g)
        except GreenletExit:
            raise
        except:
            import sys
            g_dispatcher.parent.throw(*sys.exc_info())

g_dispatcher = greenlet(dispatcher_mainloop)
#g_waiters = {}
