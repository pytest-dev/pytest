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
    WorkerPool = py._thread.WorkerPool 
    NamedThreadPool = py._thread.NamedThreadPool 

import os
debug = 0 # open('/tmp/execnet-debug-%d' % os.getpid()  , 'wa')

sysex = (KeyboardInterrupt, SystemExit)

class Gateway(object):
    _ThreadOut = ThreadOut 
    remoteaddress = ""
    def __init__(self, io, execthreads=None, _startcount=2): 
        """ initialize core gateway, using the given 
            inputoutput object and 'execthreads' execution
            threads. 
        """
        global registered_cleanup
        self._execpool = WorkerPool(maxthreads=execthreads)
        self._io = io
        self._outgoing = Queue.Queue()
        self._channelfactory = ChannelFactory(self, _startcount)
        if not registered_cleanup:
            atexit.register(cleanup_atexit)
            registered_cleanup = True
        _active_sendqueues[self._outgoing] = True
        self._pool = NamedThreadPool(receiver = self._thread_receiver, 
                                     sender = self._thread_sender)

    def __repr__(self):
        """ return string representing gateway type and status. """
        addr = self.remoteaddress 
        if addr:
            addr = '[%s]' % (addr,)
        else:
            addr = ''
        try:
            r = (len(self._pool.getstarted('receiver'))
                 and "receiving" or "not receiving")
            s = (len(self._pool.getstarted('sender')) 
                 and "sending" or "not sending")
            i = len(self._channelfactory.channels())
        except AttributeError:
            r = s = "uninitialized"
            i = "no"
        return "<%s%s %s/%s (%s active channels)>" %(
                self.__class__.__name__, addr, r, s, i)

##    def _local_trystopexec(self):
##        self._execpool.shutdown() 

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
                    raise
                except EOFError:
                    break
                except:
                    self._traceex(exc_info())
                    break 
        finally:
            self._outgoing.put(None)
            self._channelfactory._finished_receiving()
            self._trace('leaving %r' % threading.currentThread())

    def _thread_sender(self):
        """ thread to send Messages over the wire. """
        try:
            from sys import exc_info
            while 1:
                msg = self._outgoing.get()
                try:
                    if msg is None:
                        self._io.close_write()
                        break
                    msg.writeto(self._io)
                except:
                    excinfo = exc_info()
                    self._traceex(excinfo)
                    if msg is not None:
                        msg.post_sent(self, excinfo)
                    raise
                else:
                    self._trace('sent -> %r' % msg)
                    msg.post_sent(self)
        finally:
            self._trace('leaving %r' % threading.currentThread())

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

    def _thread_executor(self, channel, (source, outid, errid)):
        """ worker thread to execute source objects from the execution queue. """
        from sys import exc_info
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
            raise
        except:
            excinfo = exc_info()
            l = traceback.format_exception(*excinfo)
            errortext = "".join(l)
            channel.close(errortext)
            self._trace(errortext)
        else:
            channel.close()

    def _local_schedulexec(self, channel, sourcetask): 
        self._trace("dispatching exec")
        self._execpool.dispatch(self._thread_executor, channel, sourcetask) 

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
        self._outgoing.put(Message.CHANNEL_OPEN(channel.id, 
                               (source, outid, errid)))
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
            c.waitclose(1.0) 
        class Handle: 
            def close(_): 
                for name, out in ('stdout', stdout), ('stderr', stderr): 
                    if out: 
                        c = self.remote_exec("""
                            import sys
                            channel.gateway._ThreadOut(sys, %r).resetdefault()
                        """ % name) 
                        c.waitclose(1.0) 
        return Handle()

    def exit(self):
        """ Try to stop all IO activity. """
        try:
            del _active_sendqueues[self._outgoing]
        except KeyError:
            pass
        else:
            self._outgoing.put(None)

    def join(self, joinexec=True):
        """ Wait for all IO (and by default all execution activity) 
            to stop. 
        """
        current = threading.currentThread()
        for x in self._pool.getstarted(): 
            if x != current: 
                self._trace("joining %s" % x)
                x.join()
        self._trace("joining sender/reciver threads finished, current %r" % current) 
        if joinexec: 
            self._execpool.join()
            self._trace("joining execution threads finished, current %r" % current) 

def getid(gw, cache={}):
    name = gw.__class__.__name__
    try:
        return cache.setdefault(name, {})[id(gw)]
    except KeyError:
        cache[name][id(gw)] = x = "%s:%s.%d" %(os.getpid(), gw.__class__.__name__, len(cache[name]))
        return x

registered_cleanup = False
_active_sendqueues = weakref.WeakKeyDictionary()
def cleanup_atexit():
    if debug:
        print >>debug, "="*20 + "cleaning up" + "=" * 20
        debug.flush()
    while True:
        try:
            queue, ignored = _active_sendqueues.popitem()
        except KeyError:
            break
        queue.put(None)
