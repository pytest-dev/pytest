"""
base gateway code 

# note that the whole code of this module (as well as some
# other modules) execute not only on the local side but 
# also on any gateway's remote side.  On such remote sides
# we cannot assume the py library to be there and 
# InstallableGateway._remote_bootstrap_gateway() (located 
# in register.py) will take care to send source fragments
# to the other side.  Yes, it is fragile but we have a 
# few tests that try to catch when we mess up. 

"""
import sys, os, weakref, atexit
import threading, traceback, socket, struct
try:
    import queue 
except ImportError:
    import Queue as queue

# XXX the following lines should not be here
if 'ThreadOut' not in globals(): 
    import py 
    from py.code import Source
    ThreadOut = py._thread.ThreadOut 

if sys.version_info > (3, 0):
    exec("""def do_exec(co, loc):
    exec(co, loc)""")
else:
    exec("""def do_exec(co, loc):
    exec co in loc""")

import os
debug = 0 # open('/tmp/execnet-debug-%d' % os.getpid()  , 'wa')

sysex = (KeyboardInterrupt, SystemExit)

# ___________________________________________________________________________
#
# input output classes
# ___________________________________________________________________________

class SocketIO:
    server_stmt = "io = SocketIO(clientsock)"

    error = (socket.error, EOFError)
    def __init__(self, sock):
        self.sock = sock
        try:
            sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_IP, socket.IP_TOS, 0x10)# IPTOS_LOWDELAY
        except socket.error:
            e = sys.exc_info()[1]
            py.builtin.print_("WARNING: Cannot set socket option:", str(e))
        self.readable = self.writeable = True

    def read(self, numbytes):
        "Read exactly 'bytes' bytes from the socket."
        buf = ""
        while len(buf) < numbytes:
            t = self.sock.recv(numbytes - len(buf))
            if not t:
                raise EOFError
            buf += t
        return buf

    def write(self, data):
        self.sock.sendall(data)

    def close_read(self):
        if self.readable:
            try:
                self.sock.shutdown(0)
            except socket.error:
                pass
            self.readable = None
    def close_write(self):
        if self.writeable:
            try:
                self.sock.shutdown(1)
            except socket.error:
                pass
            self.writeable = None

class Popen2IO:
    server_stmt = """
import os, sys, StringIO
io = Popen2IO(sys.stdout, sys.stdin)
sys.stdout = sys.stderr = StringIO.StringIO() 
"""
    error = (IOError, OSError, EOFError)

    def __init__(self, infile, outfile):
        self.outfile, self.infile = infile, outfile
        if sys.platform == "win32":
            import msvcrt
            msvcrt.setmode(infile.fileno(), os.O_BINARY)
            msvcrt.setmode(outfile.fileno(), os.O_BINARY)

        self.readable = self.writeable = True

    def read(self, numbytes):
        """Read exactly 'bytes' bytes from the pipe. """
        s = self.infile.read(numbytes)
        if len(s) < numbytes:
            raise EOFError
        return s

    def write(self, data):
        """write out all bytes to the pipe. """
        self.outfile.write(data)
        self.outfile.flush()

    def close_read(self):
        if self.readable:
            self.infile.close()
            self.readable = None
    def close_write(self):
        try:
            self.outfile.close()
        except EnvironmentError:
            pass
        self.writeable = None

# ___________________________________________________________________________
#
# Messages
# ___________________________________________________________________________
# the header format
HDR_FORMAT = "!hhii"
HDR_SIZE   = struct.calcsize(HDR_FORMAT)

class Message:
    """ encapsulates Messages and their wire protocol. """
    _types = {}
    def __init__(self, channelid=0, data=''):
        self.channelid = channelid
        self.data = data

    def writeto(self, io):
        # XXX marshal.dumps doesn't work for exchanging data across Python
        # version :-(((  There is no sane solution, short of a custom
        # pure Python marshaller
        data = self.data
        if isinstance(data, str):
            dataformat = 1
        else:
            data = repr(self.data)  # argh
            dataformat = 2
        header = struct.pack(HDR_FORMAT, self.msgtype, dataformat,
                                         self.channelid, len(data))
        io.write(header + data)

    def readfrom(cls, io):
        header = io.read(HDR_SIZE)
        (msgtype, dataformat,
         senderid, stringlen) = struct.unpack(HDR_FORMAT, header)
        data = io.read(stringlen)
        if dataformat == 1:
            pass
        elif dataformat == 2:
            data = eval(data, {})   # reversed argh
        else:
            raise ValueError("bad data format")
        msg = cls._types[msgtype](senderid, data)
        return msg
    readfrom = classmethod(readfrom)

    def post_sent(self, gateway, excinfo=None):
        pass

    def __repr__(self):
        r = repr(self.data)
        if len(r) > 50:
            return "<Message.%s channelid=%d len=%d>" %(self.__class__.__name__,
                        self.channelid, len(r))
        else:
            return "<Message.%s channelid=%d %r>" %(self.__class__.__name__,
                        self.channelid, self.data)


def _setupmessages():
    # XXX use metaclass for registering 

    class CHANNEL_OPEN(Message):
        def received(self, gateway):
            channel = gateway._channelfactory.new(self.channelid)
            gateway._local_schedulexec(channel=channel, sourcetask=self.data)

    class CHANNEL_NEW(Message):
        def received(self, gateway):
            """ receive a remotely created new (sub)channel. """
            newid = self.data
            newchannel = gateway._channelfactory.new(newid)
            gateway._channelfactory._local_receive(self.channelid, newchannel)

    class CHANNEL_DATA(Message):
        def received(self, gateway):
            gateway._channelfactory._local_receive(self.channelid, self.data)

    class CHANNEL_CLOSE(Message):
        def received(self, gateway):
            gateway._channelfactory._local_close(self.channelid)

    class CHANNEL_CLOSE_ERROR(Message):
        def received(self, gateway):
            remote_error = gateway._channelfactory.RemoteError(self.data)
            gateway._channelfactory._local_close(self.channelid, remote_error)

    class CHANNEL_LAST_MESSAGE(Message):
        def received(self, gateway):
            gateway._channelfactory._local_last_message(self.channelid)

    classes = [CHANNEL_OPEN, CHANNEL_NEW, CHANNEL_DATA, 
               CHANNEL_CLOSE, CHANNEL_CLOSE_ERROR, CHANNEL_LAST_MESSAGE]
            
    for i, cls in enumerate(classes):
        Message._types[i] = cls
        cls.msgtype = i
        setattr(Message, cls.__name__, cls)

_setupmessages()


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
        self._items = queue.Queue()
        self._closed = False
        self._receiveclosed = threading.Event()
        self._remoteerrors = []

    def setcallback(self, callback, endmarker=NO_ENDMARKER_WANTED):
        items = self._items
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
                    olditem = items.get(block=False)
                except queue.Empty:
                    break
                else:
                    if olditem is ENDMARKER:
                        items.put(olditem)
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
            raise IOError("Timeout")
        error = self._getremoteerror()
        if error:
            raise error

    def send(self, item):
        """sends the given item to the other side of the channel,
        possibly blocking if the sender queue is full.
        Note that an item needs to be marshallable.
        """
        if self.isclosed(): 
            raise IOError("cannot send to %r" %(self,))
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
         


# ----------------------------------------------------------
# cleanup machinery (for exiting processes) 
# ----------------------------------------------------------

class GatewayCleanup:
    def __init__(self): 
        self._activegateways = weakref.WeakKeyDictionary()
        atexit.register(self.cleanup_atexit)

    def register(self, gateway):
        assert gateway not in self._activegateways
        self._activegateways[gateway] = True

    def unregister(self, gateway):
        del self._activegateways[gateway]

    def cleanup_atexit(self):
        if debug:
            print >>debug, "="*20 + "cleaning up" + "=" * 20
            debug.flush()
        for gw in self._activegateways.keys():
            gw.exit()
            #gw.join() # should work as well

class ExecnetAPI:
    def pyexecnet_gateway_init(self, gateway):
        """ signal initialisation of new gateway. """ 
    def pyexecnet_gateway_exit(self, gateway):
        """ signal exitting of gateway. """ 

    def pyexecnet_gwmanage_newgateway(self, gateway, platinfo):
        """ called when a manager has made a new gateway. """ 

    def pyexecnet_gwmanage_rsyncstart(self, source, gateways):
        """ called before rsyncing a directory to remote gateways takes place. """

    def pyexecnet_gwmanage_rsyncfinish(self, source, gateways):
        """ called after rsyncing a directory to remote gateways takes place. """

        
        
class BaseGateway(object):

    class _StopExecLoop(Exception): pass
    _ThreadOut = ThreadOut 
    remoteaddress = ""
    _requestqueue = None
    _cleanup = GatewayCleanup()

    def __init__(self, io, _startcount=2): 
        """ initialize core gateway, using the given inputoutput object. 
        """
        self._io = io
        self._channelfactory = ChannelFactory(self, _startcount)
        self._cleanup.register(self) 
        if _startcount == 1: # only import 'py' on the "client" side 
            import py
            self.hook = py._com.HookRelay(ExecnetAPI, py._com.comregistry)
        else:
            self.hook = ExecnetAPI()

    def _initreceive(self, requestqueue=False):
        if requestqueue: 
            self._requestqueue = queue.Queue()
        self._receiverthread = threading.Thread(name="receiver", 
                                 target=self._thread_receiver)
        self._receiverthread.setDaemon(1)
        self._receiverthread.start() 

    def __repr__(self):
        """ return string representing gateway type and status. """
        addr = self.remoteaddress 
        if addr:
            addr = '[%s]' % (addr,)
        else:
            addr = ''
        try:
            r = (self._receiverthread.isAlive() and "receiving" or 
                 "not receiving")
            s = "sending" # XXX
            i = len(self._channelfactory.channels())
        except AttributeError:
            r = s = "uninitialized"
            i = "no"
        return "<%s%s %s/%s (%s active channels)>" %(
                self.__class__.__name__, addr, r, s, i)

    def _trace(self, *args):
        if debug:
            try:
                l = "\n".join(args).split(os.linesep)
                id = getid(self)
                for x in l:
                    print >>debug, x
                debug.flush()
            except sysex:
                raise
            except:
                traceback.print_exc()

    def _traceex(self, excinfo):
        try:
            l = traceback.format_exception(*excinfo)
            errortext = "".join(l)
        except:
            errortext = '%s: %s' % (excinfo[0].__name__,
                                    excinfo[1])
        self._trace(errortext)

    def _thread_receiver(self):
        """ thread to read and handle Messages half-sync-half-async. """
        try:
            from sys import exc_info
            while 1:
                try:
                    msg = Message.readfrom(self._io)
                    self._trace("received <- %r" % msg)
                    msg.received(self)
                except sysex:
                    break
                except EOFError:
                    break
                except:
                    self._traceex(exc_info())
                    break 
        finally:
            # XXX we need to signal fatal error states to
            #     channels/callbacks, particularly ones 
            #     where the other side just died. 
            self._stopexec()
            try:
                self._stopsend()
            except IOError: 
                self._trace('IOError on _stopsend()')
            self._channelfactory._finished_receiving()
            if threading: # might be None during shutdown/finalization
                self._trace('leaving %r' % threading.currentThread())

    from sys import exc_info
    def _send(self, msg):
        if msg is None:
            self._io.close_write()
        else:
            try:
                msg.writeto(self._io) 
            except: 
                excinfo = self.exc_info()
                self._traceex(excinfo)
                msg.post_sent(self, excinfo)
            else:
                msg.post_sent(self)
                self._trace('sent -> %r' % msg)

    def _local_redirect_thread_output(self, outid, errid): 
        l = []
        for name, id in ('stdout', outid), ('stderr', errid): 
            if id: 
                channel = self._channelfactory.new(outid)
                out = self._ThreadOut(sys, name)
                out.setwritefunc(channel.send) 
                l.append((out, channel))
        def close(): 
            for out, channel in l: 
                out.delwritefunc() 
                channel.close() 
        return close 

    def _local_schedulexec(self, channel, sourcetask):
        if self._requestqueue is not None:
            self._requestqueue.put((channel, sourcetask)) 
        else:
            # we will not execute, let's send back an error
            # to inform the other side
            channel.close("execution disallowed")

    def _servemain(self, joining=True):
        from sys import exc_info
        self._initreceive(requestqueue=True)
        try:
            while 1:
                item = self._requestqueue.get()
                if item is None:
                    self._stopsend()
                    break
                try:
                    self._executetask(item)
                except self._StopExecLoop:
                    break
        finally:
            self._trace("_servemain finished") 
        if joining:
            self.join()

    def _executetask(self, item):
        """ execute channel/source items. """
        from sys import exc_info
        channel, (source, outid, errid) = item 
        try:
            loc = { 'channel' : channel, '__name__': '__channelexec__'}
            #open("task.py", 'w').write(source)
            self._trace("execution starts:", repr(source)[:50])
            close = self._local_redirect_thread_output(outid, errid) 
            try:
                co = compile(source+'\n', '', 'exec')
                do_exec(co, loc)
            finally:
                close() 
                self._trace("execution finished:", repr(source)[:50])
        except (KeyboardInterrupt, SystemExit):
            pass 
        except self._StopExecLoop:
            channel.close()
            raise
        except:
            excinfo = exc_info()
            l = traceback.format_exception(*excinfo)
            errortext = "".join(l)
            channel.close(errortext)
            self._trace(errortext)
        else:
            channel.close()

    def _newredirectchannelid(self, callback): 
        if callback is None: 
            return  
        if hasattr(callback, 'write'): 
            callback = callback.write 
        assert callable(callback) 
        chan = self.newchannel()
        chan.setcallback(callback)
        return chan.id 

    def _rinfo(self, update=False):
        """ return some sys/env information from remote. """
        if update or not hasattr(self, '_cache_rinfo'):
            class RInfo:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
                def __repr__(self):
                    info = ", ".join(["%s=%s" % item 
                            for item in self.__dict__.items()])
                    return "<RInfo %r>" % info
            self._cache_rinfo = RInfo(**self.remote_exec("""
                import sys, os
                channel.send(dict(
                    executable = sys.executable, 
                    version_info = sys.version_info, 
                    platform = sys.platform,
                    cwd = os.getcwd(),
                    pid = os.getpid(),
                ))
            """).receive())
        return self._cache_rinfo

    # _____________________________________________________________________
    #
    # High Level Interface
    # _____________________________________________________________________
    #
    def remote_exec(self, source, stdout=None, stderr=None): 
        """ return channel object and connect it to a remote
            execution thread where the given 'source' executes
            and has the sister 'channel' object in its global 
            namespace.  The callback functions 'stdout' and 
            'stderr' get called on receival of remote 
            stdout/stderr output strings. 
        """
        try:
            source = str(Source(source))
        except NameError: 
            try: 
                import py 
                source = str(py.code.Source(source))
            except ImportError: 
                pass 
        channel = self.newchannel() 
        outid = self._newredirectchannelid(stdout) 
        errid = self._newredirectchannelid(stderr) 
        self._send(Message.CHANNEL_OPEN(
                    channel.id, (source, outid, errid)))
        return channel 

    def remote_init_threads(self, num=None):
        """ start up to 'num' threads for subsequent 
            remote_exec() invocations to allow concurrent
            execution. 
        """
        if hasattr(self, '_remotechannelthread'):
            raise IOError("remote threads already running")
        from py.__.thread import pool
        source = py.code.Source(pool, """
            execpool = WorkerPool(maxthreads=%r)
            gw = channel.gateway
            while 1:
                task = gw._requestqueue.get()
                if task is None:
                    gw._stopsend()
                    execpool.shutdown()
                    execpool.join()
                    raise gw._StopExecLoop
                execpool.dispatch(gw._executetask, task)
        """ % num)
        self._remotechannelthread = self.remote_exec(source)

    def newchannel(self): 
        """ return new channel object.  """ 
        return self._channelfactory.new()

    def join(self, joinexec=True):
        """ Wait for all IO (and by default all execution activity) 
            to stop. the joinexec parameter is obsolete. 
        """
        current = threading.currentThread()
        if self._receiverthread.isAlive():
            self._trace("joining receiver thread")
            self._receiverthread.join()

    def exit(self):
        """ Try to stop all exec and IO activity. """
        self._cleanup.unregister(self)
        self._stopexec()
        self._stopsend()
        self.hook.pyexecnet_gateway_exit(gateway=self)

    def _remote_redirect(self, stdout=None, stderr=None): 
        """ return a handle representing a redirection of a remote 
            end's stdout to a local file object.  with handle.close() 
            the redirection will be reverted.   
        """ 
        clist = []
        for name, out in ('stdout', stdout), ('stderr', stderr): 
            if out: 
                outchannel = self.newchannel()
                outchannel.setcallback(getattr(out, 'write', out))
                channel = self.remote_exec(""" 
                    import sys
                    outchannel = channel.receive() 
                    outchannel.gateway._ThreadOut(sys, %r).setdefaultwriter(outchannel.send)
                """ % name) 
                channel.send(outchannel)
                clist.append(channel)
        for c in clist: 
            c.waitclose() 
        class Handle: 
            def close(_): 
                for name, out in ('stdout', stdout), ('stderr', stderr): 
                    if out: 
                        c = self.remote_exec("""
                            import sys
                            channel.gateway._ThreadOut(sys, %r).resetdefault()
                        """ % name) 
                        c.waitclose() 
        return Handle()


    def _stopsend(self):
        self._send(None)

    def _stopexec(self):
        if self._requestqueue is not None:
            self._requestqueue.put(None)

def getid(gw, cache={}):
    name = gw.__class__.__name__
    try:
        return cache.setdefault(name, {})[id(gw)]
    except KeyError:
        cache[name][id(gw)] = x = "%s:%s.%d" %(os.getpid(), gw.__class__.__name__, len(cache[name]))
        return x

