import thread, sys

__all__ = ['greenlet', 'main', 'getcurrent']


class greenlet(object):
    __slots__ = ('run', '_controller')

    def __init__(self, run=None, parent=None):
        if run is not None:
            self.run = run
        if parent is not None:
            self.parent = parent

    def switch(self, *args):
        global _passaround_
        _passaround_ = None, args, None
        self._controller.switch(self)
        exc, val, tb = _passaround_
        del _passaround_
        if exc is None:
            if isinstance(val, tuple) and len(val) == 1:
                return val[0]
            else:
                return val
        else:
            raise exc, val, tb

    def __nonzero__(self):
        return self._controller.isactive()

    def __new__(cls, *args, **kwds):
        self = object.__new__(cls)
        self._controller = _Controller()
        return self

    def __del__(self):
        #print 'DEL:', self
        if self._controller.parent is None:
            return   # don't kill the main greenlet
        while self._controller.isactive():
            self._controller.kill(self)

    def getparent(self):
        return self._controller.parent

    def setparent(self, nparent):
        if not isinstance(nparent, greenlet):
            raise TypeError, "parent must be a greenlet"
        p = nparent
        while p is not None:
            if p is self:
                raise ValueError, "cyclic parent chain"
            p = p._controller.parent
        self._controller.parent = nparent

    parent = property(getparent, setparent)
    del getparent
    del setparent


class _Controller:
    # Controllers are separated from greenlets to allow greenlets to be
    # deallocated while running, when their last reference goes away.
    # Care is taken to keep only references to controllers in thread's
    # frames' local variables.

    # _Controller.parent: the parent greenlet.
    # _Controller.lock: the lock used for synchronization
    #                   it is not set before the greenlet starts
    #                   it is None after the greenlet stops

    def __init__(self):
        self.parent = _current_

    def isactive(self):
        return getattr(self, 'lock', None) is not None

    def switch(self, target):
        previous = _current_._controller
        self.switch_no_wait(target)
        # wait until someone releases this thread's lock
        previous.lock.acquire()

    def switch_no_wait(self, target):
        # lock tricks: each greenlet has its own lock which is almost always
        # in 'acquired' state:
        # * the current greenlet runs with its lock acquired
        # * all other greenlets wait on their own lock's acquire() call
        global _current_
        try:
            while 1:
                _current_ = target
                lock = self.lock
                if lock is not None:
                    break
                target = self.parent
                self = target._controller
        except AttributeError:
            # start the new greenlet
            lock = self.lock = thread.allocate_lock()
            lock.acquire()
            thread.start_new_thread(self.run_thread, (target.run,))
        else:
            # release (re-enable) the target greenlet's thread
            lock.release()

    def run_thread(self, run):
        #print 'ENTERING', self
        global _passaround_
        exc, val, tb = _passaround_
        if exc is None:
            try:
                result = run(*val)
            except SystemExit, e:
                _passaround_ = None, (e,), None
            except:
                _passaround_ = sys.exc_info()
            else:
                _passaround_ = None, (result,), None
        self.lock = None
        #print 'LEAVING', self
        self.switch_no_wait(self.parent)

    def kill(self, target):
        # see comments in greenlet.c:green_dealloc()
        global _passaround_
        self._parent_ = _current_
        _passaround_ = SystemExit, None, None
        self.switch(target)
        exc, val, tb = _passaround_
        del _passaround_
        if exc is not None:
            if val is None:
                print >> sys.stderr, "Exception", "%s" % (exc,),
            else:
                print >> sys.stderr, "Exception", "%s: %s" % (exc, val),
            print >> sys.stderr, "in", self, "ignored"


_current_ = None
main = greenlet()
main._controller.lock = thread.allocate_lock()
main._controller.lock.acquire()
_current_ = main

def getcurrent():
    return _current_
