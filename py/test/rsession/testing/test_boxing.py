
""" test boxing functionality
"""

import py, sys, os

if sys.platform == 'win32':
    py.test.skip("rsession is unsupported on Windows.")

from py.__.test.rsession.box import Box
from py.__.test.rsession.testing import example2

def setup_module(mod):
    tmpdir = py.test.ensuretemp("boxtests")
    mod.config = py.test.config._reparse([tmpdir])

def test_basic_boxing():
    # XXX: because we do not have option transfer
##    if not hasattr(option, 'nocapture') or not option.nocapture:
##        py.test.skip("Interacts with pylib i/o skipping which is bad actually")
    b = Box(example2.boxf1, config=config)
    b.run()
    assert b.stdoutrepr == "some out\n"
    assert b.stderrrepr == "some err\n"
    assert b.exitstat == 0
    assert b.signal == 0
    assert b.retval == 1

def test_boxing_on_fds():
    b = Box(example2.boxf2, config=config)
    b.run()
    assert b.stdoutrepr == "someout"
    assert b.stderrrepr == "someerr"
    assert b.exitstat == 0
    assert b.signal == 0
    assert b.retval == 2

def test_boxing_signal():
    b = Box(example2.boxseg, config=config)
    b.run()
    assert b.retval is None
    if py.std.sys.version_info < (2,4):
        py.test.skip("signal detection does not work with python prior 2.4")
    assert b.signal == 11

def test_boxing_huge_data():
    b = Box(example2.boxhuge, config=config)
    b.run()
    assert b.stdoutrepr
    assert b.exitstat == 0
    assert b.signal == 0
    assert b.retval == 3

def test_box_seq():
    # we run many boxes with huge data, just one after another
    for i in xrange(100):
        b = Box(example2.boxhuge, config=config)
        b.run()
        assert b.stdoutrepr
        assert b.exitstat == 0
        assert b.signal == 0
        assert b.retval == 3

def test_box_in_a_box():
    def boxfun():
        b = Box(example2.boxf2, config=config)
        b.run()
        print b.stdoutrepr
        print >>sys.stderr, b.stderrrepr
        return b.retval
    
    b = Box(boxfun, config=config)
    b.run()
    assert b.stdoutrepr == "someout\n"
    assert b.stderrrepr == "someerr\n"
    assert b.exitstat == 0
    assert b.signal == 0
    assert b.retval == 2

def test_box_killer():
    class A:
        pass
    info = A()
    import time

    def box_fun():
        time.sleep(10) # we don't want to last forever here
    
    b = Box(box_fun, config=config)
    par, pid = b.run(continuation=True)
    os.kill(pid, 15)
    par(pid)
    if py.std.sys.version_info < (2,4):
        py.test.skip("signal detection does not work with python prior 2.4")
    assert b.signal == 15
