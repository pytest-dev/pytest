import py

def test_make_sdist_and_run_it(py_setup, venv):
    sdist = py_setup.make_sdist(venv.path)
    venv.easy_install(str(sdist)) 
    gw = venv.makegateway()
    ch = gw.remote_exec("import py ; channel.send(py.__version__)")
    version = ch.receive()
    assert version == py.__version__
