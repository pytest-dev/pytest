""" 
    tests for py.execnet.GatewaySpec
"""

import py

class TestGatewaySpec:
    """
    socket:hostname:port:path SocketGateway
    popen[-executable][:path] PopenGateway
    [ssh:]spec:path           SshGateway
    * [SshGateway]
    """
    def test_popen(self):
        for python in ('', 'python2.4'):
            for joinpath in ('', 'abc', 'ab:cd', '/x/y'):
                s = ":".join(["popen", python, joinpath])
                print s
                spec = py.execnet.GatewaySpec(s)
                assert spec.address == "popen"
                assert spec.python == (python or py.std.sys.executable)
                assert spec.joinpath == joinpath
                assert spec.type == "popen"
                spec2 = py.execnet.GatewaySpec("popen" + joinpath)
                self._equality(spec, spec2)

    def test_ssh(self):
        for prefix in ('ssh', ''): # ssh is default
            for hostpart in ('x.y', 'xyz@x.y'):
                for python in ('python', 'python2.5'):
                    for joinpath in ('', 'abc', 'ab:cd', '/tmp'):
                        specstring = ":".join([prefix, hostpart, python, joinpath])
                        if specstring[0] == ":":
                            specstring = specstring[1:]
                        print specstring
                        spec = py.execnet.GatewaySpec(specstring)
                        assert spec.address == hostpart 
                        assert spec.python == python
                        if joinpath:
                            assert spec.joinpath == joinpath
                        else:
                            assert spec.joinpath == "pyexecnetcache"
                        assert spec.type == "ssh"
                        spec2 = py.execnet.GatewaySpec(specstring)
                        self._equality(spec, spec2) 
    
    def test_socket(self):
        for hostpart in ('x.y', 'x', 'popen'):
            for port in ":80", ":1000":
                for joinpath in ('', ':abc', ':abc:de'):
                    spec = py.execnet.GatewaySpec("socket:" + hostpart + port + joinpath)
                    assert spec.address == (hostpart, int(port[1:]))
                    if joinpath[1:]:
                        assert spec.joinpath == joinpath[1:]
                    else:
                        assert spec.joinpath == "pyexecnetcache"
                    assert spec.type == "socket"
                    spec2 = py.execnet.GatewaySpec("socket:" + hostpart + port + joinpath)
                    self._equality(spec, spec2) 

    def _equality(self, spec1, spec2):
        assert spec1 != spec2
        assert hash(spec1) != hash(spec2)
        assert not (spec1 == spec2)


class TestGatewaySpecAPI:
    def test_popen_nopath_makegateway(self, testdir):
        spec = py.execnet.GatewaySpec("popen")
        gw = spec.makegateway()
        p = gw.remote_exec("import os; channel.send(os.getcwd())").receive()
        curdir = py.std.os.getcwd()
        assert curdir == p
        gw.exit()

    def test_popen_makegateway(self, testdir):
        spec = py.execnet.GatewaySpec("popen::" + str(testdir.tmpdir))
        gw = spec.makegateway()
        p = gw.remote_exec("import os; channel.send(os.getcwd())").receive()
        assert spec.joinpath == p
        gw.exit()

    def test_popen_makegateway_python(self, testdir):
        spec = py.execnet.GatewaySpec("popen:%s" % py.std.sys.executable)
        gw = spec.makegateway()
        res = gw.remote_exec("import sys ; channel.send(sys.executable)").receive()
        assert py.std.sys.executable == py.std.sys.executable
        gw.exit()

    def test_ssh(self, specssh):
        sshhost = specssh.ssh
        spec = py.execnet.GatewaySpec("ssh:" + sshhost)
        gw = spec.makegateway()
        p = gw.remote_exec("import os ; channel.send(os.getcwd())").receive()
        gw.exit()

    @py.test.mark.xfail("implement socketserver test scenario")
    def test_socketgateway(self):
        gw = py.execnet.PopenGateway()
        spec = py.execnet.GatewaySpec("ssh:" + sshhost)

