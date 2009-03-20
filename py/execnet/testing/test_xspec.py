import py

XSpec = py.execnet.XSpec

class TestXSpec:
    def test_attributes(self):
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

    def test__samefilesystem(self):
        assert XSpec("popen")._samefilesystem()
        assert XSpec("popen//python=123")._samefilesystem()
        assert not XSpec("popen//path=hello")._samefilesystem()

class TestMakegateway:
    def test_popen(self):
        gw = py.execnet.makegateway("popen")
        assert gw.spec.python == None
        rinfo = gw._rinfo()
        assert rinfo.executable == py.std.sys.executable 
        assert rinfo.cwd == py.std.os.getcwd()
        assert rinfo.version_info == py.std.sys.version_info

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
                break
        else:
            py.test.skip("cpython2.4 not found")
        gw = py.execnet.makegateway("popen//python=%s" % cpython24)
        rinfo = gw._rinfo()
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
