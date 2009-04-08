"""
TODO:
    + switching on this plugin breaks 'setup_method' mechanism which then is not previously called before the test function.
    + credits to Ralf Schmitt See: http://twistedmatrix.com/pipermail/twisted-python/2007-February/014872.html
    + add option for twisted logging
    + write tests
"""

import os
import sys

import py
try:
    from twisted.internet.defer import Deferred
except ImportError:
    print "To use the twisted option you have to install twisted."
    sys.exit(0)
try:
    from greenlet import greenlet
except ImportError:
    print "Since pylib 1.0 greenlet are removed and separately packaged: " \
            "http://pypi.python.org/pypi/greenlet" 
    sys.exit(0)

DIR_CUR = str(py.path.local())


def _start_twisted_logging():
    class Logger(object):
        """late-bound sys.stdout"""
        def write(self, msg):
            sys.stdout.write(msg)

        def flush(self):
            sys.stdout.flush()
            # sys.stdout will be changed by py.test later.

    import twisted.python.log
    twisted.python.log.startLogging(Logger(), setStdout=0)

def _run_twisted():
    """greenlet: run twisted mainloop"""
    from twisted.internet import reactor, defer
    from twisted.python import log, failure
    failure.Failure.cleanFailure = lambda *args: None # make twisted copy traceback...
    _start_twisted_logging() # XXX: add py.test option
    
    def doit(val):
        res = gr_tests.switch(val)
        if res is None:
            reactor.stop()
            return
            
        def done(res):
            reactor.callLater(0.0, doit, None)

        def err(res):
            reactor.callLater(0.0, doit, res)
            
        defer.maybeDeferred(res).addCallback(done).addErrback(err)
        
    reactor.callLater(0.0, doit, None)
    reactor.run()


class TwistedPlugin:
    """Allows to test twisted applications with pytest."""

    def pytest_addoption(self, parser):
        parser.addoption("--twisted", dest="twisted", 
            help="Allows to test twisted applications with pytest.")

    def pytest_configure(self, config):
        twisted = config.getvalue("twisted")
        if twisted:
            print "Twisted plugin switched on"
            gr_twisted.switch()

    def pytest_unconfigure(self, config):
        gr_twisted.switch(None)

    def pytest_pyfunc_call(self, pyfuncitem, *args, **kwargs):
        def wrapper(func):
            res = func.obj()
            if isinstance(res, Deferred):
                res = gr_twisted.switch(func.obj)
                if res:
                    res.raiseException()
            return res
        pyfuncitem = wrapper(pyfuncitem)    


gr_twisted  = greenlet(_run_twisted)
gr_tests    = greenlet.getcurrent()

# ===============================================================================
# plugin tests 
# ===============================================================================

# XXX: write test
'''
def test_generic(plugintester):
    plugintester.apicheck(EventlogPlugin)

    testdir = plugintester.testdir()
    testdir.makepyfile("""
        def test_pass():
            pass
    """)
    testdir.runpytest("--twisted")
    s = testdir.tmpdir.join("event.log").read()
    assert s.find("TestrunStart") != -1
    assert s.find("ItemTestReport") != -1
    assert s.find("TestrunFinish") != -1
'''
