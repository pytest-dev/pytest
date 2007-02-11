import py
from py.process import cmdexec

class Test_exec_cmd:
    def test_simple(self):
        out = cmdexec('echo hallo')
        assert out.strip() == 'hallo'

    def test_simple_error(self):
        py.test.raises (cmdexec.Error, cmdexec, 'exit 1')

    def test_simple_error_exact_status(self):
        try:
            cmdexec('exit 1')
        except cmdexec.Error, e:
            assert e.status == 1

    def test_err(self):
        try:
            cmdexec('echoqweqwe123 hallo')
            raise AssertionError, "command succeeded but shouldn't"
        except cmdexec.Error, e:
            assert hasattr(e, 'err')
            assert hasattr(e, 'out')
            assert e.err or e.out

def test_cmdexec_selection():
    from py.__.process import cmdexec 
    if py.std.sys.platform == "win32":
        assert py.process.cmdexec == cmdexec.win32_exec_cmd
    elif hasattr(py.std.sys, 'pypy') or hasattr(py.std.sys, 'pypy_objspaceclass'):
        assert py.process.cmdexec == cmdexec.popen3_exec_cmd
    else:
        assert py.process.cmdexec == cmdexec.posix_exec_cmd
        
        
        
    
