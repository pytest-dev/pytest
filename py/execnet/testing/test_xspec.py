import py

def test_XSpec_attributes():
    XSpec = py.execnet.XSpec
    spec = XSpec("socket=192.168.102.2:8888//python=c:/this/python2.5//path=d:\hello")
    assert spec.socket == "192.168.102.2:8888"
    assert spec.python == "c:/this/python2.5" 
    assert spec.path == "d:\hello"
    assert spec.xyz is None

    py.test.raises(AttributeError, "spec._hello")

    spec = XSpec("socket=192.168.102.2:8888//python=python2.5")
    assert spec.socket == "192.168.102.2:8888"
    assert spec.python == "python2.5"
    assert spec.path is None

    spec = XSpec("ssh=user@host//path=/hello/this//python=/usr/bin/python2.5")
    assert spec.ssh == "user@host"
    assert spec.python == "/usr/bin/python2.5"
    assert spec.path == "/hello/this"

    spec = XSpec("popen")
    assert spec.popen == True

@py.test.mark.xfail
def test_makegateway_popen():
    spec = py.execnet.XSpec("popen")
    gw = py.execnet.makegateway(spec)
    assert gw.spec == spec
    rinfo = gw.remote_info()
    assert rinfo.executable == py.std.sys.executable 
    assert rinfo.curdir == py.std.os.getcwd()
    assert rinfo.version_info == py.std.sys.version_info
