from py import test
from py.process import cmdexec

class Test_exec_cmd:
    def test_simple(self):
        out = cmdexec('echo hallo')
        assert out.strip() == 'hallo'

    def test_simple_error(self):
        test.raises (cmdexec.Error, cmdexec, 'exit 1')

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
