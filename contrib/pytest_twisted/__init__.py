"""
Allows to test twisted applications with pytest.

Notes: twisted's asynchronous behavior may have influence on the order of test-functions

TODO:
    + credits to Ralf Schmitt See: http://twistedmatrix.com/pipermail/twisted-python/2007-February/014872.html
    + get test to work
"""

import sys

try:
    from twisted.internet import reactor, defer
    from twisted.python import failure, log
except ImportError:
    print "To use the twisted option you have to install twisted."
    sys.exit(10)
try:
    from greenlet import greenlet
except ImportError:
    print "Since pylib 1.0 greenlet are removed and separately packaged: " \
            "http://pypi.python.org/pypi/greenlet" 
    sys.exit(10)


def _start_twisted_logging():
    """Enables twisted internal logging"""

    class Logger(object):
        """late-bound sys.stdout"""
        def write(self, msg):
            sys.stdout.write(msg)

        def flush(self):
            sys.stdout.flush()
            # sys.stdout will be changed by py.test later.
    log.startLogging(Logger(), setStdout=0)

def _run_twisted(logging=False):
    """Start twisted mainloop and initialize recursive calling of doit()."""

    # make twisted copy traceback...
    failure.Failure.cleanFailure = lambda *args: None
    if logging:
        _start_twisted_logging()
        
    def fix_signal_handling():
        # see http://twistedmatrix.com/trac/ticket/733
        import signal
        if hasattr(signal, "siginterrupt"):
            signal.siginterrupt(signal.SIGCHLD, False)

    def start():
        fix_signal_handling()
        doit(None)
        
    # recursively called for each test-function/method due done()
    def doit(val): # val always None
        # switch context to wait that wrapper() passes back to test-method
        res = gr_tests.switch(val)
        if res is None:
            reactor.stop()
            return

        def done(res):
            reactor.callLater(0.0, doit, None) # recursive call of doit()

        def err(res):
            reactor.callLater(0.0, doit, res)
            
        # the test-function *may* return a deferred
        # here the test-function will actually been called
        # done() is finalizing a test-process by assuring recursive invoking
        # of doit()
        defer.maybeDeferred(res).addCallback(done).addErrback(err)
    # initially preparing the calling of doit() and starting the reactor
    reactor.callLater(0.0, start)
    reactor.run()

def pytest_addoption(parser):
    group = parser.addgroup('twisted options')
    group.addoption('--twisted-logging', action='store_true', default=False,
            dest='twisted_logging',
            help="switch on twisted internal logging")

def pytest_configure(config):
    twisted_logging = config.getvalue("twisted_logging")
    gr_twisted.switch(twisted_logging)

def pytest_unconfigure(config):
    gr_twisted.switch(None)

def pytest_pyfunc_call(pyfuncitem):
    # XXX1 kwargs?  
    # XXX2 we want to delegate actual call to next plugin
    #      (which may want to produce test coverage, etc.) 
    res = gr_twisted.switch(lambda: pyfuncitem.call())
    if res:
        res.raiseException()
    return True # indicates that we performed the function call 

gr_twisted  = greenlet(_run_twisted)
gr_tests    = greenlet.getcurrent()

# ===============================================================================
# plugin tests 
# ===============================================================================

def test_generic(testdir):
    testdir.makepyfile('''
        def test_pass():
            pass
        from twisted.internet import defer, reactor
        from twisted.python import failure
        from twisted.python import log


        def test_no_deferred():
            assert True is True

        def test_deferred():
            log.msg("test_deferred() called")
            d = defer.Deferred()
            def done():
                log.msg("test_deferred.done() CALLBACK DONE")
                d.callback(None)
                
            reactor.callLater(2.5, done)
            log.msg("test_deferred() returning deferred: %r" % (d,))
            return d

        def test_deferred2():
            log.msg("test_deferred2() called")
            d = defer.Deferred()
            def done():
                log.msg("test_deferred2.done() CALLBACK DONE")
                d.callback(None)
                
            reactor.callLater(2.5, done)
            log.msg("test_deferred2() returning deferred: %r" % (d,))
            return d

        def test_deferred4():
            log.msg("test_deferred4() called")
            from twisted.web.client import getPage
            def printContents(contents):
                assert contents == ""

            deferred = getPage('http://twistedmatrix.com/')
            deferred.addCallback(printContents)
            return deferred

        def test_deferred3():
            log.msg("test_deferred3() called")
            d = defer.Deferred()
            def done():
                log.msg("test_deferred3.done() CALLBACK DONE")
                d.callback(None)
                
            reactor.callLater(2.5, done)
            log.msg("test_deferred3() returning deferred: %r" % (d,))
            return d

        class TestTwistedSetupMethod:
            def setup_method(self, method):
                log.msg("TestTwistedSetupMethod.setup_method() called")

            def test_deferred(self):
                log.msg("TestTwistedSetupMethod.test_deferred() called")
                d = defer.Deferred()
                def done():
                    log.msg("TestTwistedSetupMethod.test_deferred() CALLBACK DONE")
                    d.callback(None)
                    
                reactor.callLater(2.5, done)
                log.msg("TestTwistedSetupMethod.test_deferred() returning deferred: %r" % (d,))
                return d


        def test_defer_fail():
            def fun():
                log.msg("provoking NameError")
                rsdfg
            return defer.maybeDeferred(fun)
    ''')
    testdir.runpytest("-T")
    # XXX: what to do?
    # s = testdir.tmpdir.join("event.log").read()
    # assert s.find("TestrunFinish") != -1
