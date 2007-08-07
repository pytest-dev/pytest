from __future__ import generators
import os, sys, time, signal
import py
from py.__.execnet import gateway
from py.__.conftest import option 
mypath = py.magic.autopath()

from StringIO import StringIO
from py.__.execnet.register import startup_modules, getsource 

TESTTIMEOUT = 10.0 # seconds

def test_getsource_import_modules(): 
    for dottedname in startup_modules: 
        yield getsource, dottedname 

def test_getsource_no_colision(): 
    seen = {}
    for dottedname in startup_modules: 
        mod = __import__(dottedname, None, None, ['__doc__'])
        for name, value in vars(mod).items(): 
            if py.std.inspect.isclass(value): 
                if name in seen: 
                    olddottedname, oldval = seen[name]
                    if oldval is not value: 
                        py.test.fail("duplicate class %r in %s and %s" % 
                                     (name, dottedname, olddottedname)) 
                seen[name] = (dottedname, value) 

def test_stdouterrin_setnull():
    cap = py.io.StdCaptureFD()
    from py.__.execnet.register import stdouterrin_setnull
    stdouterrin_setnull()
    import os
    os.write(1, "hello")
    if os.name == "nt":
        os.write(2, "world")
    os.read(0, 1)
    out, err = cap.reset()
    assert not out
    assert not err


class TestMessage:
    def test_wire_protocol(self):
        for cls in gateway.Message._types.values():
            one = StringIO()
            cls(42, '23').writeto(one)
            two = StringIO(one.getvalue())
            msg = gateway.Message.readfrom(two)
            assert isinstance(msg, cls)
            assert msg.channelid == 42
            assert msg.data == '23'
            assert isinstance(repr(msg), str)
            # == "<Message.%s channelid=42 '23'>" %(msg.__class__.__name__, )

class TestPureChannel:
    def setup_method(self, method):
        self.fac = gateway.ChannelFactory(None)

    def test_factory_create(self):
        chan1 = self.fac.new()
        assert chan1.id == 1
        chan2 = self.fac.new()
        assert chan2.id == 3

    def test_factory_getitem(self):
        chan1 = self.fac.new()
        assert self.fac._channels[chan1.id] == chan1
        chan2 = self.fac.new()
        assert self.fac._channels[chan2.id] == chan2

    def test_channel_timeouterror(self):
        channel = self.fac.new()
        py.test.raises(IOError, channel.waitclose, timeout=0.01)

class PopenGatewayTestSetup:
    def setup_class(cls):
        cls.gw = py.execnet.PopenGateway()

    #def teardown_class(cls):
    #    cls.gw.exit()

class BasicRemoteExecution:
    def test_correct_setup(self):
        assert self.gw._receiverthread.isAlive()

    def test_repr_doesnt_crash(self):
        assert isinstance(repr(self), str)

    def test_correct_setup_no_py(self):
        channel = self.gw.remote_exec("""
            import sys
            channel.send(sys.modules.keys())
        """) 
        remotemodules = channel.receive() 
        assert 'py' not in remotemodules, (
                "py should not be imported on remote side") 

    def test_remote_exec_waitclose(self):
        channel = self.gw.remote_exec('pass')
        channel.waitclose(TESTTIMEOUT)

    def test_remote_exec_waitclose_2(self):
        channel = self.gw.remote_exec('def gccycle(): pass')
        channel.waitclose(TESTTIMEOUT)

    def test_remote_exec_waitclose_noarg(self):
        channel = self.gw.remote_exec('pass')
        channel.waitclose()

    def test_remote_exec_error_after_close(self):
        channel = self.gw.remote_exec('pass')
        channel.waitclose(TESTTIMEOUT)
        py.test.raises(IOError, channel.send, 0)

    def test_remote_exec_channel_anonymous(self):
        channel = self.gw.remote_exec('''
                    obj = channel.receive()
                    channel.send(obj)
                  ''')
        channel.send(42)
        result = channel.receive()
        assert result == 42

    def test_channel_close_and_then_receive_error(self):
        channel = self.gw.remote_exec('raise ValueError')
        py.test.raises(channel.RemoteError, channel.receive)

    def test_channel_finish_and_then_EOFError(self):
        channel = self.gw.remote_exec('channel.send(42)') 
        x = channel.receive()
        assert x == 42
        py.test.raises(EOFError, channel.receive) 
        py.test.raises(EOFError, channel.receive) 
        py.test.raises(EOFError, channel.receive) 

    def test_channel_close_and_then_receive_error_multiple(self):
        channel = self.gw.remote_exec('channel.send(42) ; raise ValueError')
        x = channel.receive()
        assert x == 42
        py.test.raises(channel.RemoteError, channel.receive)

    def test_channel__local_close(self):
        channel = self.gw._channelfactory.new()
        self.gw._channelfactory._local_close(channel.id)
        channel.waitclose(0.1)

    def test_channel__local_close_error(self):
        channel = self.gw._channelfactory.new()
        self.gw._channelfactory._local_close(channel.id,
                                            channel.RemoteError("error"))
        py.test.raises(channel.RemoteError, channel.waitclose, 0.01)

    def test_channel_error_reporting(self):
        channel = self.gw.remote_exec('def foo():\n  return foobar()\nfoo()\n')
        try:
            channel.receive()
        except channel.RemoteError, e:
            assert str(e).startswith('Traceback (most recent call last):')
            assert str(e).find('NameError: global name \'foobar\' '
                               'is not defined') > -1
        else:
            py.test.fail('No exception raised')

    def test_channel_syntax_error(self):
        # missing colon
        channel = self.gw.remote_exec('def foo()\n return 1\nfoo()\n')
        try:
            channel.receive()
        except channel.RemoteError, e:
            assert str(e).startswith('Traceback (most recent call last):')
            assert str(e).find('SyntaxError') > -1

    def test_channel_iter(self):
        channel = self.gw.remote_exec("""
              for x in range(3): 
                channel.send(x)
        """) 
        l = list(channel) 
        assert l == range(3) 

    def test_channel_passing_over_channel(self):
        channel = self.gw.remote_exec('''
                    c = channel.gateway.newchannel()
                    channel.send(c)
                    c.send(42)
                  ''')
        c = channel.receive()
        x = c.receive()
        assert x == 42

        # check that the both sides previous channels are really gone
        channel.waitclose(TESTTIMEOUT)
        #assert c.id not in self.gw._channelfactory
        newchan = self.gw.remote_exec('''
                    assert %d not in channel.gateway._channelfactory._channels
                  ''' % (channel.id))
        newchan.waitclose(TESTTIMEOUT)
        assert channel.id not in self.gw._channelfactory._channels

    def test_channel_receiver_callback(self): 
        l = []
        #channel = self.gw.newchannel(receiver=l.append)
        channel = self.gw.remote_exec(source='''
            channel.send(42)
            channel.send(13)
            channel.send(channel.gateway.newchannel())
            ''') 
        channel.setcallback(callback=l.append)
        py.test.raises(IOError, channel.receive)
        channel.waitclose(TESTTIMEOUT)
        assert len(l) == 3
        assert l[:2] == [42,13]
        assert isinstance(l[2], channel.__class__) 

    def test_channel_callback_after_receive(self):
        l = []
        channel = self.gw.remote_exec(source='''
            channel.send(42)
            channel.send(13)
            channel.send(channel.gateway.newchannel())
            ''') 
        x = channel.receive()
        assert x == 42
        channel.setcallback(callback=l.append)
        py.test.raises(IOError, channel.receive)
        channel.waitclose(TESTTIMEOUT) 
        assert len(l) == 2
        assert l[0] == 13
        assert isinstance(l[1], channel.__class__) 

    def test_waiting_for_callbacks(self):
        l = []
        def callback(msg):
            import time; time.sleep(0.2)
            l.append(msg)
        channel = self.gw.remote_exec(source='''
            channel.send(42)
            ''')
        channel.setcallback(callback)
        channel.waitclose(TESTTIMEOUT) 
        assert l == [42]

    def test_channel_callback_stays_active(self, earlyfree=True):
        # with 'earlyfree==True', this tests the "sendonly" channel state.
        l = []
        channel = self.gw.remote_exec(source='''
            import thread, time
            def producer(subchannel):
                for i in range(5):
                    time.sleep(0.15)
                    subchannel.send(i*100)
            channel2 = channel.receive()
            thread.start_new_thread(producer, (channel2,))
            del channel2
            ''')
        subchannel = self.gw.newchannel()
        subchannel.setcallback(l.append)
        channel.send(subchannel)
        if earlyfree:
            subchannel = None
        counter = 100
        while len(l) < 5:
            if subchannel and subchannel.isclosed():
                break
            counter -= 1
            print counter
            if not counter:
                py.test.fail("timed out waiting for the answer[%d]" % len(l))
            time.sleep(0.04)   # busy-wait
        assert l == [0, 100, 200, 300, 400]
        return subchannel

    def test_channel_callback_remote_freed(self):
        channel = self.test_channel_callback_stays_active(False)
        channel.waitclose(TESTTIMEOUT) # freed automatically at the end of producer()

    def test_channel_endmarker_callback(self):
        l = []
        channel = self.gw.remote_exec(source='''
            channel.send(42)
            channel.send(13)
            channel.send(channel.gateway.newchannel())
            ''') 
        channel.setcallback(l.append, 999)
        py.test.raises(IOError, channel.receive)
        channel.waitclose(TESTTIMEOUT)
        assert len(l) == 4
        assert l[:2] == [42,13]
        assert isinstance(l[2], channel.__class__) 
        assert l[3] == 999

    def test_remote_redirect_stdout(self): 
        out = py.std.StringIO.StringIO() 
        handle = self.gw._remote_redirect(stdout=out) 
        c = self.gw.remote_exec("print 42")
        c.waitclose(TESTTIMEOUT)
        handle.close() 
        s = out.getvalue() 
        assert s.strip() == "42" 

    def test_remote_exec_redirect_multi(self): 
        num = 3
        l = [[] for x in range(num)]
        channels = [self.gw.remote_exec("print %d" % i, 
                                        stdout=l[i].append)
                        for i in range(num)]
        for x in channels: 
            x.waitclose(TESTTIMEOUT) 

        for i in range(num): 
            subl = l[i] 
            assert subl 
            s = subl[0]
            assert s.strip() == str(i)

    def test_channel_file(self): 
        channel = self.gw.remote_exec("""
            f = channel.makefile() 
            print >>f, "hello world" 
            f.close() 
            channel.send(42) 
        """)
        first = channel.receive() + channel.receive()
        assert first.strip() == 'hello world' 
        second = channel.receive() 
        assert second == 42 

    def test_channel_file_write_error(self): 
        channel = self.gw.remote_exec("pass") 
        f = channel.makefile() 
        channel.waitclose(TESTTIMEOUT)
        py.test.raises(IOError, f.write, 'hello')

    def test_channel_file_proxyclose(self): 
        channel = self.gw.remote_exec("""
            f = channel.makefile(proxyclose=True) 
            print >>f, "hello world" 
            f.close() 
            channel.send(42) 
        """)
        first = channel.receive() + channel.receive()
        assert first.strip() == 'hello world' 
        py.test.raises(EOFError, channel.receive)

    def test_confusion_from_os_write_stdout(self):
        channel = self.gw.remote_exec("""
            import os
            os.write(1, 'confusion!')
            channel.send(channel.receive() * 6)
            channel.send(channel.receive() * 6)
        """)
        channel.send(3)
        res = channel.receive()
        assert res == 18
        channel.send(7)
        res = channel.receive()
        assert res == 42

    def test_confusion_from_os_write_stderr(self):
        channel = self.gw.remote_exec("""
            import os
            os.write(2, 'test')
            channel.send(channel.receive() * 6)
            channel.send(channel.receive() * 6)
        """)
        channel.send(3)
        res = channel.receive()
        assert res == 18
        channel.send(7)
        res = channel.receive()
        assert res == 42

    def test_non_reverse_execution(self):
        gw = self.gw
        c1 = gw.remote_exec("""
            c = channel.gateway.remote_exec("pass")
            try:
                c.waitclose()
            except c.RemoteError, e: 
                channel.send(str(e))
        """)
        text = c1.receive()
        assert text.find("execution disallowed") != -1 
    
#class TestBlockingIssues: 
#    def test_join_blocked_execution_gateway(self): 
#        gateway = py.execnet.PopenGateway() 
#        channel = gateway.remote_exec("""
#            time.sleep(5.0)
#        """)
#        def doit(): 
#            gateway.exit() 
#            gateway.join(joinexec=True) 
#            return 17 
#
#        pool = py._thread.WorkerPool() 
#        reply = pool.dispatch(doit) 
#        x = reply.get(timeout=1.0) 
#        assert x == 17 

class TestPopenGateway(PopenGatewayTestSetup, BasicRemoteExecution):
    #disabled = True
    def test_chdir_separation(self):
        old = py.test.ensuretemp('chdirtest').chdir()
        try:
            gw = py.execnet.PopenGateway()
        finally:
            waschangedir = old.chdir()
        c = gw.remote_exec("import os ; channel.send(os.getcwd())")
        x = c.receive()
        assert x == str(waschangedir)
        
    def test_many_popen(self):
        num = 4
        l = []
        for i in range(num):
            l.append(py.execnet.PopenGateway())
        channels = []
        for gw in l:
            channel = gw.remote_exec("""channel.send(42)""")
            channels.append(channel)
##        try:
##            while channels:
##                channel = channels.pop()
##                try:
##                    ret = channel.receive()
##                    assert ret == 42
##                finally:
##                    channel.gateway.exit()
##        finally:
##            for x in channels:
##                x.gateway.exit()
        while channels:
            channel = channels.pop()
            ret = channel.receive()
            assert ret == 42
            
    def disabled_test_remote_is_killed_while_sending(self):
        gw = py.execnet.PopenGateway()
        channel = gw.remote_exec("""
            import os
            import time
            channel.send(os.getppid())
            channel.send(os.getpid())
            while 1:
                channel.send('#'*1000)
            time.sleep(10)
        """)
        parent = channel.receive()
        remote = channel.receive()
        assert parent == os.getpid()
        time.sleep(0.5) 
        os.kill(remote, signal.SIGKILL)
        time.sleep(1)
        channel.waitclose(TESTTIMEOUT)
        py.test.raises(EOFError, channel.receive)
        #channel.waitclose(TESTTIMEOUT)
        #channel.send('#')
        
        

class SocketGatewaySetup:
    def setup_class(cls):
        # open a gateway to a fresh child process
        cls.proxygw = py.execnet.PopenGateway() 
        cls.gw = py.execnet.SocketGateway.new_remote(cls.proxygw,
                                                     ("127.0.0.1", 0)
                                                     ) 

##    def teardown_class(cls):
##        cls.gw.exit()
##        cls.proxygw.exit()

class TestSocketGateway(SocketGatewaySetup, BasicRemoteExecution):
    pass

class TestSshGateway(BasicRemoteExecution):
    def setup_class(cls): 
        if option.sshtarget is None: 
            py.test.skip("no known ssh target, use -S to set one")
        cls.gw = py.execnet.SshGateway(option.sshtarget) 

    def test_sshaddress(self):
        assert self.gw.remoteaddress == option.sshtarget

    def test_failed_connexion(self):
        gw = py.execnet.SshGateway('nowhere.codespeak.net')
        try:
            channel = gw.remote_exec("...")
        except IOError:
            pass      # connexion failed already
        else:
            # connexion did not fail yet
            py.test.raises(EOFError, channel.receive)
            # now it did
            py.test.raises(IOError, gw.remote_exec, "...")

def test_threads():
    gw = py.execnet.PopenGateway()
    gw.remote_init_threads(3)
    c1 = gw.remote_exec("channel.send(channel.receive())")
    c2 = gw.remote_exec("channel.send(channel.receive())")
    c2.send(1)
    res = c2.receive()
    assert res == 1
    c1.send(42)
    res = c1.receive()
    assert res == 42
    gw.exit()

def test_threads_twice():
    gw = py.execnet.PopenGateway()
    gw.remote_init_threads(3)
    py.test.raises(IOError, gw.remote_init_threads, 3)
    gw.exit() 
    
    
