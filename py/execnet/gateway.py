import os
import threading
import Queue
import traceback
import atexit
import weakref
import __future__

# note that the whole code of this module (as well as some
# other modules) execute not only on the local side but 
# also on any gateway's remote side.  On such remote sides
# we cannot assume the py library to be there and 
# InstallableGateway._remote_bootstrap_gateway() (located 
# in register.py) will take care to send source fragments
# to the other side.  Yes, it is fragile but we have a 
# few tests that try to catch when we mess up. 

# XXX the following lines should not be here
if 'ThreadOut' not in globals(): 
    import py 
    from py.code import Source
    from py.__.execnet.channel import ChannelFactory, Channel
    from py.__.execnet.message import Message
    ThreadOut = py._thread.ThreadOut 

import os
debug = 0 # open('/tmp/execnet-debug-%d' % os.getpid()  , 'wa')

sysex = (KeyboardInterrupt, SystemExit)

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

# ----------------------------------------------------------
# Base Gateway (used for both remote and local side) 
# ----------------------------------------------------------

class Gateway(object):
    class _StopExecLoop(Exception): pass
    _ThreadOut = ThreadOut 
    remoteaddress = ""
    _requestqueue = None
    _cleanup = GatewayCleanup()

    def __init__(self, io, _startcount=2): 
        """ initialize core gateway, using the given 
            inputoutput object. 
        """
        self._io = io
        self._channelfactory = ChannelFactory(self, _startcount)
        self._cleanup.register(self) 

    def _initreceive(self, requestqueue=False):
        if requestqueue: 
            self._requestqueue = Queue.Queue()
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

    def _executetask(self, item):
        """ execute channel/source items. """
        from sys import exc_info
        channel, (source, outid, errid) = item 
        try:
            loc = { 'channel' : channel }
            self._trace("execution starts:", repr(source)[:50])
            close = self._local_redirect_thread_output(outid, errid) 
            try:
                co = compile(source+'\n', '', 'exec',
                             __future__.CO_GENERATOR_ALLOWED)
                exec co in loc
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

    # _____________________________________________________________________
    #
    # High Level Interface
    # _____________________________________________________________________
    #
    def newchannel(self): 
        """ return new channel object.  """ 
        return self._channelfactory.new()

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

    def exit(self):
        """ Try to stop all exec and IO activity. """
        self._cleanup.unregister(self)
        self._stopexec()
        self._stopsend()

    def _stopsend(self):
        self._send(None)

    def _stopexec(self):
        if self._requestqueue is not None:
            self._requestqueue.put(None)

    def join(self, joinexec=True):
        """ Wait for all IO (and by default all execution activity) 
            to stop. the joinexec parameter is obsolete. 
        """
        current = threading.currentThread()
        if self._receiverthread.isAlive():
            self._trace("joining receiver thread")
            self._receiverthread.join()

def getid(gw, cache={}):
    name = gw.__class__.__name__
    try:
        return cache.setdefault(name, {})[id(gw)]
    except KeyError:
        cache[name][id(gw)] = x = "%s:%s.%d" %(os.getpid(), gw.__class__.__name__, len(cache[name]))
        return x

