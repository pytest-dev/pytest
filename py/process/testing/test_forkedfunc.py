import py, sys, os

def setup_module(mod):
    if not hasattr(os, 'fork'):
        py.test.skip("forkedfunc requires os.fork")
    mod.tmpdir = py.test.ensuretemp(mod.__file__)

def test_waitfinish_removes_tempdir():
    ff = py.process.ForkedFunc(boxf1)
    assert ff.tempdir.check()
    ff.waitfinish()
    assert not ff.tempdir.check()

def test_tempdir_gets_gc_collected():
    ff = py.process.ForkedFunc(boxf1)
    assert ff.tempdir.check()
    ff.__del__()
    assert not ff.tempdir.check()
    os.waitpid(ff.pid, 0)

def test_basic_forkedfunc():
    result = py.process.ForkedFunc(boxf1).waitfinish()
    assert result.out == "some out\n"
    assert result.err == "some err\n"
    assert result.exitstatus == 0
    assert result.signal == 0
    assert result.retval == 1

def test_exitstatus():
    def func():
        os._exit(4)
    result = py.process.ForkedFunc(func).waitfinish()
    assert result.exitstatus == 4
    assert result.signal == 0
    assert not result.out 
    assert not result.err 

def test_execption_in_func():
    def fun():
        raise ValueError(42)
    ff = py.process.ForkedFunc(fun)
    result = ff.waitfinish()
    assert result.exitstatus == ff.EXITSTATUS_EXCEPTION
    assert result.err.find("ValueError: 42") != -1
    assert result.signal == 0
    assert not result.retval

def test_forkedfunc_on_fds():
    result = py.process.ForkedFunc(boxf2).waitfinish()
    assert result.out == "someout"
    assert result.err == "someerr"
    assert result.exitstatus == 0
    assert result.signal == 0
    assert result.retval == 2

def test_forkedfunc_signal():
    result = py.process.ForkedFunc(boxseg).waitfinish()
    assert result.retval is None
    if py.std.sys.version_info < (2,4):
        py.test.skip("signal detection does not work with python prior 2.4")
    assert result.signal == 11

def test_forkedfunc_huge_data():
    result = py.process.ForkedFunc(boxhuge).waitfinish()
    assert result.out
    assert result.exitstatus == 0
    assert result.signal == 0
    assert result.retval == 3

def test_box_seq():
    # we run many boxes with huge data, just one after another
    for i in xrange(50):
        result = py.process.ForkedFunc(boxhuge).waitfinish()
        assert result.out
        assert result.exitstatus == 0
        assert result.signal == 0
        assert result.retval == 3

def test_box_in_a_box():
    def boxfun():
        result = py.process.ForkedFunc(boxf2).waitfinish()
        print result.out
        print >>sys.stderr, result.err
        return result.retval
    
    result = py.process.ForkedFunc(boxfun).waitfinish()
    assert result.out == "someout\n"
    assert result.err == "someerr\n"
    assert result.exitstatus == 0
    assert result.signal == 0
    assert result.retval == 2

def test_kill_func_forked():
    class A:
        pass
    info = A()
    import time

    def box_fun():
        time.sleep(10) # we don't want to last forever here
    
    ff = py.process.ForkedFunc(box_fun)
    os.kill(ff.pid, 15)
    result = ff.waitfinish()
    if py.std.sys.version_info < (2,4):
        py.test.skip("signal detection does not work with python prior 2.4")
    assert result.signal == 15



# ======================================================================
# examples 
# ======================================================================
#

def boxf1():
    print "some out"
    print >>sys.stderr, "some err"
    return 1

def boxf2():
    os.write(1, "someout")
    os.write(2, "someerr")
    return 2

def boxseg():
    os.kill(os.getpid(), 11)

def boxhuge():
    os.write(1, " " * 10000)
    os.write(2, " " * 10000)
    os.write(1, " " * 10000)
    
    os.write(1, " " * 10000)
    os.write(2, " " * 10000)
    os.write(2, " " * 10000)
    os.write(1, " " * 10000)
    return 3
