import py
from pygreen.greenexecnet import *
import pygreen

def setup_module(mod):
    os.environ["PYTHONPATH"] = "%s:%s" %(
            py.path.local(pygreen.__file__).dirpath().dirpath(), os.environ['PYTHONPATH'])
    #py.test.skip("need to fix PYTHONPATH/sys.path handling for sub processes so "
    #             "that they find the pygreen package.")

def test_simple():
    gw = PopenGateway()
    channel = gw.remote_exec("x = channel.receive(); channel.send(x * 6)")
    channel.send(7)
    res = channel.receive()
    assert res == 42

def test_ssh():
    py.test.skip("Bootstrapping")
    gw = SshGateway('codespeak.net')
    channel = gw.remote_exec("""
        import socket
        channel.send(socket.gethostname())
    """)
    res = channel.receive()
    assert res.endswith('codespeak.net')

def test_remote_error():
    gw = PopenGateway()
    channel = gw.remote_exec("x = channel.receive(); channel.send(x + 1)")
    channel.send("hello")
    py.test.raises(RemoteError, channel.receive)

def test_invalid_object():
    class X(object):
        pass
    gw = PopenGateway()
    channel = gw.remote_exec("x = channel.receive(); channel.send(x + 1)")
    channel.send(X())
    py.test.raises(RemoteError, channel.receive)

def test_channel_over_channel():
    gw = PopenGateway()
    chan1 = gw.newchannel()
    channel = gw.remote_exec("chan1 = channel.receive(); chan1.send(42)")
    channel.send(chan1)
    res = chan1.receive()
    assert res == 42
