import Queue 
import threading
import time 
import sys

ERRORMARKER = object() 

class Reply(object): 
    """ reply instances provide access to the result
        of a function execution that got dispatched
        through WorkerPool.dispatch() 
    """
    _excinfo = None 
    def __init__(self, task): 
        self.task = task 
        self._queue = Queue.Queue() 

    def _set(self, result): 
        self._queue.put(result) 

    def _setexcinfo(self, excinfo): 
        self._excinfo = excinfo 
        self._queue.put(ERRORMARKER) 

    def _get_with_timeout(self, timeout): 
        # taken from python2.3's Queue.get() 
        # we want to run on python2.2 here
        delay = 0.0005 # 500 us -> initial delay of 1 ms
        endtime = time.time() + timeout
        while 1:
            try: 
                return self._queue.get_nowait() 
            except Queue.Empty: 
                remaining = endtime - time.time() 
                if remaining <= 0:  #time is over and no element arrived
                    raise IOError("timeout waiting for task %r" %(self.task,))
                delay = min(delay * 2, remaining, .05)
                time.sleep(delay)       #reduce CPU usage by using a sleep

    def get(self, timeout=None): 
        """ get the result object from an asynchronous function execution.
            if the function execution raised an exception, 
            then calling get() will reraise that exception
            including its traceback. 
        """
        if self._queue is None: 
            raise EOFError("reply has already been delivered")
        if timeout is not None: 
            result = self._get_with_timeout(timeout) 
        else: 
            result = self._queue.get() 
        if result is ERRORMARKER: 
            self._queue = None
            excinfo = self._excinfo 
            raise excinfo[0], excinfo[1], excinfo[2]
        return result 

class WorkerThread(threading.Thread): 
    def __init__(self, pool): 
        threading.Thread.__init__(self) 
        self._queue = Queue.Queue() 
        self._pool = pool 
        self.setDaemon(1) 

    def _run_once(self):
        reply = self._queue.get()
        if reply is SystemExit:
            return False
        assert self not in self._pool._ready 
        task = reply.task 
        try: 
            func, args, kwargs = task 
            result = func(*args, **kwargs) 
        except (SystemExit, KeyboardInterrupt): 
            return False
        except: 
            reply._setexcinfo(sys.exc_info()) 
        else: 
            reply._set(result) 
        # at this point, reply, task and all other local variables go away
        return True

    def run(self): 
        try: 
            while self._run_once():
                self._pool._ready[self] = True 
        finally: 
            del self._pool._alive[self]
            try: 
                del self._pool._ready[self]
            except KeyError: 
                pass

    def send(self, task): 
        reply = Reply(task) 
        self._queue.put(reply) 
        return reply 

    def stop(self): 
        self._queue.put(SystemExit)   
        
class WorkerPool(object): 
    """ A WorkerPool allows to dispatch function executions
        to threads.  Each Worker Thread is reused for multiple
        function executions. The dispatching operation 
        takes care to create and dispatch to existing 
        threads. 

        You need to call shutdown() to signal 
        the WorkerThreads to terminate and join() 
        in order to wait until all worker threads
        have terminated. 
    """
    _shuttingdown = False 
    def __init__(self, maxthreads=None): 
        """ init WorkerPool instance which may
            create up to `maxthreads` worker threads. 
        """
        self.maxthreads = maxthreads
        self._ready = {}
        self._alive = {}

    def dispatch(self, func, *args, **kwargs): 
        """ return Reply object for the asynchronous dispatch 
            of the given func(*args, **kwargs) in a 
            separate worker thread. 
        """
        if self._shuttingdown: 
            raise IOError("WorkerPool is already shutting down") 
        try: 
            thread, _ = self._ready.popitem() 
        except KeyError: # pop from empty list
            if self.maxthreads and len(self._alive) >= self.maxthreads: 
                raise IOError("can't create more than %d threads." %
                              (self.maxthreads,))
            thread = self._newthread() 
        return thread.send((func, args, kwargs))

    def _newthread(self): 
        thread = WorkerThread(self) 
        self._alive[thread] = True 
        thread.start() 
        return thread 

    def shutdown(self): 
        """ signal all worker threads to terminate. 
            call join() to wait until all threads termination. 
        """
        if not self._shuttingdown: 
            self._shuttingdown = True 
            for t in self._alive.keys(): 
                t.stop() 

    def join(self, timeout=None): 
        """ wait until all worker threads have terminated. """
        current = threading.currentThread()
        deadline = delta = None 
        if timeout is not None: 
            deadline = time.time() + timeout 
        for thread in self._alive.keys(): 
            if deadline: 
                delta = deadline - time.time() 
                if delta <= 0: 
                    raise IOError("timeout while joining threads") 
            thread.join(timeout=delta) 
            if thread.isAlive(): 
                raise IOError("timeout while joining threads") 

class NamedThreadPool: 
    def __init__(self, **kw): 
        self._namedthreads = {}
        for name, value in kw.items(): 
            self.start(name, value) 

    def __repr__(self): 
        return "<NamedThreadPool %r>" %(self._namedthreads) 

    def get(self, name=None): 
        if name is None: 
            l = []
            for x in self._namedthreads.values(): 
                l.extend(x) 
            return l 
        else: 
            return self._namedthreads.get(name, [])

    def getstarted(self, name=None): 
        return [t for t in self.get(name) if t.isAlive()]

    def prunestopped(self, name=None): 
        if name is None: 
            for name in self.names(): 
                self.prunestopped(name) 
        else: 
            self._namedthreads[name] = self.getstarted(name) 

    def names(self): 
        return self._namedthreads.keys() 

    def start(self, name, func): 
        l = self._namedthreads.setdefault(name, []) 
        thread = threading.Thread(name="%s%d" % (name, len(l)), 
                                  target=func) 
        thread.start() 
        l.append(thread) 

