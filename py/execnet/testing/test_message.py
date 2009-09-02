
import py
from py.__.execnet import gateway_base

@py.test.mark.multi(ver=["2.4", "2.5", "2.6", "3.1"])
def test_io_message(ver, tmpdir):
    executable = py.path.local.sysfind("python" + ver)
    if executable is None:
        py.test.skip("no python%s found" % (ver,))
    check = tmpdir.join("check.py")
    check.write(py.code.Source(gateway_base, """
        try:
            from io import BytesIO 
        except ImportError:
            from StringIO import StringIO as BytesIO
        import tempfile
        temp_out = BytesIO()
        temp_in = BytesIO()
        io = Popen2IO(temp_out, temp_in)
        for i, msg_cls in Message._types.items():
            print ("checking %s %s" %(i, msg_cls))
            for data in "hello", "hello".encode('ascii'):
                msg1 = msg_cls(i, data)
                msg1.writeto(io)
                x = io.outfile.getvalue()
                io.outfile.truncate(0)
                io.outfile.seek(0)
                io.infile.seek(0)
                io.infile.write(x)
                io.infile.seek(0)
                msg2 = Message.readfrom(io)
                assert msg1.channelid == msg2.channelid, (msg1, msg2)
                assert msg1.data == msg2.data
        print ("all passed")
    """))
    #out = py.process.cmdexec("%s %s" %(executable,check))
    out = executable.sysexec(check)
    print (out)
    assert "all passed" in out
