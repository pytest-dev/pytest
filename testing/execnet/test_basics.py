
import py
import sys, os, subprocess, inspect
from py.__.execnet import gateway_base, gateway
from py.__.execnet.gateway_base import Message, Channel, ChannelFactory

def test_subprocess_interaction(anypython):
    line = gateway.popen_bootstrapline
    compile(line, 'xyz', 'exec')
    args = [str(anypython), '-c', line]
    popen = subprocess.Popen(args, bufsize=0, stderr=subprocess.STDOUT,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    def send(line):
        popen.stdin.write(line.encode('ascii'))
        if sys.version_info > (3,0): # 3k still buffers 
            popen.stdin.flush()
    def receive():
        return popen.stdout.readline().decode('ascii')

    try:
        source = py.code.Source(read_write_loop, "read_write_loop()")
        repr_source = repr(str(source)) + "\n"
        sendline = repr_source
        send(sendline)    
        s = receive()
        assert s == "ok\n"
        send("hello\n")
        s = receive()
        assert s == "received: hello\n"
        send("world\n")
        s = receive()
        assert s == "received: world\n"
    finally:
        popen.stdin.close()
        popen.stdout.close()
        popen.wait()

def read_write_loop():
    import os, sys
    sys.stdout.write("ok\n")
    sys.stdout.flush()
    while 1:
        try:
            line = sys.stdin.readline()
            sys.stdout.write("received: %s" % line)
            sys.stdout.flush()
        except (IOError, EOFError):
            break

def pytest_generate_tests(metafunc):
    if 'anypython' in metafunc.funcargnames:
        for name in 'python3.1', 'python2.4', 'python2.5', 'python2.6':
            metafunc.addcall(id=name, param=name)

def pytest_funcarg__anypython(request):
    name = request.param  
    executable = py.path.local.sysfind(name)
    if executable is None:
        py.test.skip("no %s found" % (name,))
    return executable

def test_io_message(anypython, tmpdir):
    check = tmpdir.join("check.py")
    check.write(py.code.Source(gateway_base, """
        try:
            from io import BytesIO 
        except ImportError:
            from StringIO import StringIO as BytesIO
        import tempfile
        temp_out = BytesIO()
        temp_in = BytesIO()
        io = Popen2IO(temp_out, temp_in)
        for i, msg_cls in Message._types.items():
            print ("checking %s %s" %(i, msg_cls))
            for data in "hello", "hello".encode('ascii'):
                msg1 = msg_cls(i, data)
                msg1.writeto(io)
                x = io.outfile.getvalue()
                io.outfile.truncate(0)
                io.outfile.seek(0)
                io.infile.seek(0)
                io.infile.write(x)
                io.infile.seek(0)
                msg2 = Message.readfrom(io)
                assert msg1.channelid == msg2.channelid, (msg1, msg2)
                assert msg1.data == msg2.data
        print ("all passed")
    """))
    #out = py.process.cmdexec("%s %s" %(executable,check))
    out = anypython.sysexec(check)
    print (out)
    assert "all passed" in out

def test_popen_io(anypython, tmpdir):
    check = tmpdir.join("check.py")
    check.write(py.code.Source(gateway_base, """
        do_exec(Popen2IO.server_stmt, globals())
        io.write("hello".encode('ascii'))
        s = io.read(1)
        assert s == "x".encode('ascii')
    """))
    from subprocess import Popen, PIPE
    args = [str(anypython), str(check)]
    proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    proc.stdin.write("x".encode('ascii'))
    stdout, stderr = proc.communicate()
    print (stderr)
    ret = proc.wait()
    assert "hello".encode('ascii') in stdout


def test_rinfo_source(anypython, tmpdir):
    check = tmpdir.join("check.py")
    check.write(py.code.Source("""
        class Channel:
            def send(self, data):
                assert eval(repr(data), {}) == data
        channel = Channel()
        """, gateway.rinfo_source, """
        print ('all passed')
    """))
    out = anypython.sysexec(check)
    print (out)
    assert "all passed" in out

def test_geterrortext(anypython, tmpdir):
    check = tmpdir.join("check.py")
    check.write(py.code.Source(gateway_base, """
        class Arg:
            pass
        errortext = geterrortext((Arg, "1", 4))
        assert "Arg" in errortext
        import sys
        try:
            raise ValueError("17")
        except ValueError:
            excinfo = sys.exc_info()
            s = geterrortext(excinfo)
            assert "17" in s
            print ("all passed")
    """))
    out = anypython.sysexec(check)
    print (out)
    assert "all passed" in out

def test_stdouterrin_setnull():
    cap = py.io.StdCaptureFD()
    from py.__.execnet.gateway import stdouterrin_setnull
    stdouterrin_setnull()
    import os
    os.write(1, "hello".encode('ascii'))
    if os.name == "nt":
        os.write(2, "world")
    os.read(0, 1)
    out, err = cap.reset()
    assert not out
    assert not err


class TestMessage:
    def test_wire_protocol(self):
        for cls in Message._types.values():
            one = py.io.BytesIO()
            data = '23'.encode('ascii')
            cls(42, data).writeto(one)
            two = py.io.BytesIO(one.getvalue())
            msg = Message.readfrom(two)
            assert isinstance(msg, cls)
            assert msg.channelid == 42
            assert msg.data == data
            assert isinstance(repr(msg), str)
            # == "<Message.%s channelid=42 '23'>" %(msg.__class__.__name__, )

class TestPureChannel:
    def setup_method(self, method):
        self.fac = ChannelFactory(None)

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

    def test_channel_makefile_incompatmode(self):
        channel = self.fac.new()
        py.test.raises(ValueError, 'channel.makefile("rw")')


