import py

XSpec = py.execnet.XSpec

class TestXSpec:
    def test_norm_attributes(self):
        spec = XSpec("socket=192.168.102.2:8888//python=c:/this/python2.5//chdir=d:\hello")
        assert spec.socket == "192.168.102.2:8888"
        assert spec.python == "c:/this/python2.5" 
        assert spec.chdir == "d:\hello"
        assert spec.nice is None
        assert not hasattr(spec, 'xyz')

        py.test.raises(AttributeError, "spec._hello")

        spec = XSpec("socket=192.168.102.2:8888//python=python2.5//nice=3")
        assert spec.socket == "192.168.102.2:8888"
        assert spec.python == "python2.5"
        assert spec.chdir is None
        assert spec.nice == "3"

        spec = XSpec("ssh=user@host//chdir=/hello/this//python=/usr/bin/python2.5")
        assert spec.ssh == "user@host"
        assert spec.python == "/usr/bin/python2.5"
        assert spec.chdir == "/hello/this"

        spec = XSpec("popen")
        assert spec.popen == True

    def test__samefilesystem(self):
        assert XSpec("popen")._samefilesystem()
        assert XSpec("popen//python=123")._samefilesystem()
        assert not XSpec("popen//chdir=hello")._samefilesystem()

    def test__spec_spec(self):
        for x in ("popen", "popen//python=this"):
            assert XSpec(x)._spec == x

    def test_repr(self):
        for x in ("popen", "popen//python=this"):
            assert repr(XSpec(x)).find("popen") != -1

    def test_hash_equality(self):
        assert XSpec("popen") == XSpec("popen")
        assert hash(XSpec("popen")) == hash(XSpec("popen"))
        assert XSpec("popen//python=123") != XSpec("popen")
        assert hash(XSpec("socket=hello:8080")) != hash(XSpec("popen"))

class TestMakegateway:
    def test_popen(self):
        gw = py.execnet.makegateway("popen")
        assert gw.spec.python == None
        rinfo = gw._rinfo()
        assert rinfo.executable == py.std.sys.executable 
        assert rinfo.cwd == py.std.os.getcwd()
        assert rinfo.version_info == py.std.sys.version_info

    def test_popen_nice(self):
        gw = py.execnet.makegateway("popen//nice=5")
        remotenice = gw.remote_exec("""
            import os
            if hasattr(os, 'nice'):
                channel.send(os.nice(0))
            else:
                channel.send(None)
        """).receive()
        if remotenice is not None:
            assert remotenice == 5

    def test_popen_explicit(self):
        gw = py.execnet.makegateway("popen//python=%s" % py.std.sys.executable)
        assert gw.spec.python == py.std.sys.executable
        rinfo = gw._rinfo()
        assert rinfo.executable == py.std.sys.executable 
        assert rinfo.cwd == py.std.os.getcwd()
        assert rinfo.version_info == py.std.sys.version_info

    def test_popen_cpython24(self):
        for trypath in ('python2.4', r'C:\Python24\python.exe'):
            cpython24 = py.path.local.sysfind(trypath)
            if cpython24 is not None:
                cpython24 = cpython24.realpath()
                break
        else:
            py.test.skip("cpython2.4 not found")
        gw = py.execnet.makegateway("popen//python=%s" % cpython24)
        rinfo = gw._rinfo()
        if py.std.sys.platform != "darwin": # it's confusing there 
            assert rinfo.executable == cpython24  
        assert rinfo.cwd == py.std.os.getcwd()
        assert rinfo.version_info[:2] == (2,4)

    def test_popen_cpython26(self):
        for trypath in ('python2.6', r'C:\Python26\python.exe'):
            cpython26 = py.path.local.sysfind(trypath)
            if cpython26 is not None:
                break
        else:
            py.test.skip("cpython2.6 not found")
        gw = py.execnet.makegateway("popen//python=%s" % cpython26)
        rinfo = gw._rinfo()
        assert rinfo.executable == cpython26
        assert rinfo.cwd == py.std.os.getcwd()
        assert rinfo.version_info[:2] == (2,6)

    def test_popen_chdir_absolute(self, testdir):
        gw = py.execnet.makegateway("popen//chdir=%s" % testdir.tmpdir)
        rinfo = gw._rinfo()
        assert rinfo.cwd == str(testdir.tmpdir.realpath())

    def test_popen_chdir_newsub(self, testdir):
        testdir.chdir()
        gw = py.execnet.makegateway("popen//chdir=hello")
        rinfo = gw._rinfo()
        assert rinfo.cwd == str(testdir.tmpdir.join("hello").realpath())

    def test_ssh(self, specssh):
        sshhost = specssh.ssh
        gw = py.execnet.makegateway("ssh=%s" % sshhost)
        rinfo = gw._rinfo()
        gw2 = py.execnet.SshGateway(sshhost)
        rinfo2 = gw2._rinfo()
        assert rinfo.executable == rinfo2.executable
        assert rinfo.cwd == rinfo2.cwd
        assert rinfo.version_info == rinfo2.version_info

    def test_socket(self, specsocket):
        gw = py.execnet.makegateway("socket=%s" % specsocket.socket)
        rinfo = gw._rinfo()
        assert rinfo.executable 
        assert rinfo.cwd 
        assert rinfo.version_info 
        # we cannot instantiate a second gateway

        #gw2 = py.execnet.SocketGateway(*specsocket.socket.split(":"))
        #rinfo2 = gw2._rinfo()
        #assert rinfo.executable == rinfo2.executable
        #assert rinfo.cwd == rinfo2.cwd
        #assert rinfo.version_info == rinfo2.version_info
