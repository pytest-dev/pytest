import threading, weakref, sys
import Queue
if 'Message' not in globals():
    from py.__.execnet.message import Message

class RemoteError(EOFError):
    """ Contains an Exceptions from the other side. """
    def __init__(self, formatted):
        self.formatted = formatted
        EOFError.__init__(self)

    def __str__(self):
        return self.formatted

    def __repr__(self):
        return "%s: %s" %(self.__class__.__name__, self.formatted)

    def warn(self):
        # XXX do this better
        print >> sys.stderr, "Warning: unhandled %r" % (self,)

NO_ENDMARKER_WANTED = object()


class Channel(object):
    """Communication channel between two possibly remote threads of code. """
    RemoteError = RemoteError

    def __init__(self, gateway, id):
        assert isinstance(id, int)
        self.gateway = gateway
        self.id = id
        self._items = Queue.Queue()
        self._closed = False
        self._receiveclosed = threading.Event()
        self._remoteerrors = []

    def setcallback(self, callback, endmarker=NO_ENDMARKER_WANTED):
        queue = self._items
        lock = self.gateway._channelfactory._receivelock
        lock.acquire()
        try:
            _callbacks = self.gateway._channelfactory._callbacks
            dictvalue = (callback, endmarker)
            if _callbacks.setdefault(self.id, dictvalue) != dictvalue:
                raise IOError("%r has callback already registered" %(self,))
            self._items = None
            while 1:
                try:
                    olditem = queue.get(block=False)
                except Queue.Empty:
                    break
                else:
                    if olditem is ENDMARKER:
                        queue.put(olditem)
                        break
                    else:
                        callback(olditem)
            if self._closed or self._receiveclosed.isSet():
                # no need to keep a callback
                self.gateway._channelfactory._close_callback(self.id)
        finally:
            lock.release()
         
    def __repr__(self):
        flag = self.isclosed() and "closed" or "open"
        return "<Channel id=%d %s>" % (self.id, flag)

    def __del__(self):
        if self.gateway is None:   # can be None in tests
            return
        self.gateway._trace("Channel(%d).__del__" % self.id)
        # no multithreading issues here, because we have the last ref to 'self'
        if self._closed:
            # state transition "closed" --> "deleted"
            for error in self._remoteerrors:
                error.warn()
        elif self._receiveclosed.isSet():
            # state transition "sendonly" --> "deleted"
            # the remote channel is already in "deleted" state, nothing to do
            pass
        else:
            # state transition "opened" --> "deleted"
            if self._items is None:    # has_callback
                Msg = Message.CHANNEL_LAST_MESSAGE
            else:
                Msg = Message.CHANNEL_CLOSE
            self.gateway._send(Msg(self.id))

    def _getremoteerror(self):
        try:
            return self._remoteerrors.pop(0)
        except IndexError:
            return None

    #
    # public API for channel objects 
    #
    def isclosed(self):
        """ return True if the channel is closed. A closed 
            channel may still hold items. 
        """ 
        return self._closed

    def makefile(self, mode='w', proxyclose=False):
        """ return a file-like object.  
            mode: 'w' for binary writes, 'r' for binary reads 
            proxyclose: set to true if you want to have a 
            subsequent file.close() automatically close the channel. 
        """ 
        if mode == "w":
            return ChannelFileWrite(channel=self, proxyclose=proxyclose)
        elif mode == "r":
            return ChannelFileRead(channel=self, proxyclose=proxyclose)
        raise ValueError("mode %r not availabe" %(mode,))

    def close(self, error=None):
        """ close down this channel on both sides. """
        if not self._closed:
            # state transition "opened/sendonly" --> "closed"
            # threads warning: the channel might be closed under our feet,
            # but it's never damaging to send too many CHANNEL_CLOSE messages
            put = self.gateway._send 
            if error is not None:
                put(Message.CHANNEL_CLOSE_ERROR(self.id, str(error)))
            else:
                put(Message.CHANNEL_CLOSE(self.id))
            if isinstance(error, RemoteError):
                self._remoteerrors.append(error)
            self._closed = True         # --> "closed"
            self._receiveclosed.set()
            queue = self._items
            if queue is not None:
                queue.put(ENDMARKER)
            self.gateway._channelfactory._no_longer_opened(self.id)

    def waitclose(self, timeout=None):
        """ wait until this channel is closed (or the remote side
        otherwise signalled that no more data was being sent).
        The channel may still hold receiveable items, but not receive
        more.  waitclose() reraises exceptions from executing code on
        the other side as channel.RemoteErrors containing a a textual
        representation of the remote traceback.
        """
        self._receiveclosed.wait(timeout=timeout)  # wait for non-"opened" state
        if not self._receiveclosed.isSet():
            raise IOError, "Timeout"
        error = self._getremoteerror()
        if error:
            raise error

    def send(self, item):
        """sends the given item to the other side of the channel,
        possibly blocking if the sender queue is full.
        Note that an item needs to be marshallable.
        """
        if self.isclosed(): 
            raise IOError, "cannot send to %r" %(self,) 
        if isinstance(item, Channel):
            data = Message.CHANNEL_NEW(self.id, item.id)
        else:
            data = Message.CHANNEL_DATA(self.id, item)
        self.gateway._send(data)

    def receive(self):
        """receives an item that was sent from the other side,
        possibly blocking if there is none.
        Note that exceptions from the other side will be
        reraised as channel.RemoteError exceptions containing
        a textual representation of the remote traceback.
        """
        queue = self._items
        if queue is None:
            raise IOError("calling receive() on channel with receiver callback")
        x = queue.get()
        if x is ENDMARKER: 
            queue.put(x)  # for other receivers 
            raise self._getremoteerror() or EOFError()
        else: 
            return x
    
    def __iter__(self):
        return self 

    def next(self): 
        try:
            return self.receive()
        except EOFError: 
            raise StopIteration 

#
# helpers
#

ENDMARKER = object() 

class ChannelFactory(object):
    RemoteError = RemoteError

    def __init__(self, gateway, startcount=1):
        self._channels = weakref.WeakValueDictionary()
        self._callbacks = {}
        self._writelock = threading.Lock()
        self._receivelock = threading.RLock()
        self.gateway = gateway
        self.count = startcount
        self.finished = False

    def new(self, id=None):
        """ create a new Channel with 'id' (or create new id if None). """
        self._writelock.acquire()
        try:
            if self.finished:
                raise IOError("connexion already closed: %s" % (self.gateway,))
            if id is None:
                id = self.count
                self.count += 2
            channel = Channel(self.gateway, id)
            self._channels[id] = channel
            return channel
        finally:
            self._writelock.release()

    def channels(self):
        return self._channels.values()

    #
    # internal methods, called from the receiver thread 
    #
    def _no_longer_opened(self, id):
        try:
            del self._channels[id]
        except KeyError:
            pass
        self._close_callback(id)

    def _close_callback(self, id):
        try:
            callback, endmarker = self._callbacks.pop(id)
        except KeyError:
            pass
        else:
            if endmarker is not NO_ENDMARKER_WANTED:
                callback(endmarker)

    def _local_close(self, id, remoteerror=None):
        channel = self._channels.get(id)
        if channel is None:
            # channel already in "deleted" state
            if remoteerror:
                remoteerror.warn()
        else:
            # state transition to "closed" state
            if remoteerror:
                channel._remoteerrors.append(remoteerror)
            channel._closed = True          # --> "closed"
            channel._receiveclosed.set()
            queue = channel._items
            if queue is not None:
                queue.put(ENDMARKER)
        self._no_longer_opened(id)

    def _local_last_message(self, id):
        channel = self._channels.get(id)
        if channel is None:
            # channel already in "deleted" state
            pass
        else:
            # state transition: if "opened", change to "sendonly"
            channel._receiveclosed.set()
            queue = channel._items
            if queue is not None:
                queue.put(ENDMARKER)
        self._no_longer_opened(id)

    def _local_receive(self, id, data): 
        # executes in receiver thread
        self._receivelock.acquire()
        try:
            try:
                callback, endmarker = self._callbacks[id]
            except KeyError:
                channel = self._channels.get(id)
                queue = channel and channel._items
                if queue is None:
                    pass    # drop data
                else:
                    queue.put(data)
            else:
                callback(data)   # even if channel may be already closed
        finally:
            self._receivelock.release()

    def _finished_receiving(self):
        self._writelock.acquire()
        try:
            self.finished = True
        finally:
            self._writelock.release()
        for id in self._channels.keys():
            self._local_last_message(id)
        for id in self._callbacks.keys():
            self._close_callback(id)

class ChannelFile(object):
    def __init__(self, channel, proxyclose=True):
        self.channel = channel
        self._proxyclose = proxyclose 

    def close(self):
        if self._proxyclose: 
            self.channel.close()

    def __repr__(self):
        state = self.channel.isclosed() and 'closed' or 'open'
        return '<ChannelFile %d %s>' %(self.channel.id, state) 

class ChannelFileWrite(ChannelFile):
    def write(self, out):
        self.channel.send(out)

    def flush(self):
        pass

class ChannelFileRead(ChannelFile):
    def __init__(self, channel, proxyclose=True):
        super(ChannelFileRead, self).__init__(channel, proxyclose)
        self._buffer = ""

    def read(self, n):
        while len(self._buffer) < n:
            try:
                self._buffer += self.channel.receive()
            except EOFError:
                self.close() 
                break
        ret = self._buffer[:n]
        self._buffer = self._buffer[n:]
        return ret 

    def readline(self):
        i = self._buffer.find("\n")
        if i != -1:
            return self.read(i+1)
        line = self.read(len(self._buffer)+1)
        while line and line[-1] != "\n":
            c = self.read(1)
            if not c:
                break
            line += c
        return line
         
