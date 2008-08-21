import py
import sys

binpath = py.path.local(py.__file__).dirpath("bin")
binwinpath = binpath.join("win32")

def setup_module(mod):
    mod.tmpdir = py.test.ensuretemp(__name__)
    mod.iswin32 = sys.platform == "win32"

def checkmain(name):
    main = getattr(py.cmdline, name)
    assert callable(main)
    assert name[:2] == "py"
    scriptname = "py." + name[2:]
    assert binpath.join(scriptname).check()
    assert binwinpath.join(scriptname + ".cmd").check()

def checkprocess(script):
    assert script.check()
    old = tmpdir.ensure(script.basename, dir=1).chdir()
    try:
        if iswin32:
            cmd = script.basename
        else:
            cmd = "%s" %(script, )

        if script.basename.startswith("py.lookup"):
            cmd += " hello"
        print "executing", script
        try:
            py.process.cmdexec(cmd)
        except py.process.cmdexec.Error, e:
            if cmd.find("py.rest") != -1 and \
               e.out.find("module named") != -1:
                return
            raise
                
    finally:
        old.chdir()

def test_cmdline_namespace():
    for name in dir(py.cmdline):
        if name[0] != "_":
            yield checkmain, name
       
def test_script_invocation():
    if iswin32:
        for script in binwinpath.listdir("py.*"):
            assert script.ext == ".cmd"
            yield checkprocess, script 
    else:
        for script in binpath.listdir("py.*"):
            yield checkprocess, script 

