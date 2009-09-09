import py

def pytest_generate_tests(metafunc):
    if 'gw' in metafunc.funcargnames:
        if hasattr(metafunc.cls, 'gwtype'):
            gwtypes = [metafunc.cls.gwtype]
        else:
            gwtypes = ['popen', 'socket', 'ssh']
        for gwtype in gwtypes:
            metafunc.addcall(id=gwtype, param=gwtype)

def pytest_funcarg__gw(request):
    scope = "session"
    if request.param == "popen":
        return request.cached_setup(
                setup=py.execnet.PopenGateway,
                teardown=lambda gw: gw.exit(),
                extrakey=request.param,
                scope=scope)
    elif request.param == "socket":
        return request.cached_setup(
            setup=setup_socket_gateway, 
            teardown=teardown_socket_gateway,
            extrakey=request.param,
            scope=scope)
    elif request.param == "ssh":
        return request.cached_setup(
            setup=lambda: setup_ssh_gateway(request),
            teardown=lambda gw: gw.exit(),
            extrakey=request.param,
            scope=scope)

def setup_socket_gateway():
    proxygw = py.execnet.PopenGateway() 
    gw = py.execnet.SocketGateway.new_remote(proxygw, ("127.0.0.1", 0)) 
    gw.proxygw = proxygw
    return gw

def teardown_socket_gateway(gw):
    gw.exit()
    gw.proxygw.exit()

def setup_ssh_gateway(request):
    sshhost = request.getfuncargvalue('specssh').ssh
    gw = py.execnet.SshGateway(sshhost)
    return gw
