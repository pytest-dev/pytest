"""
submit failure or test session information to a pastebin service. 

Usage
----------

**Creating a URL for each test failure**::

    py.test --pastebin=failed 

This will submit test run information to a remote Paste service and
provide a URL for each failure.  You may select tests as usual or add
for example ``-x`` if you only want to send one particular failure. 

**Creating a URL for a whole test session log**::

    py.test --pastebin=all 

Currently only pasting to the http://paste.pocoo.org service is implemented.  

"""
import py, sys

class url:
    base = "http://paste.pocoo.org"
    xmlrpc = base + "/xmlrpc/"
    show = base + "/show/"

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group._addoption('--pastebin', metavar="mode",
        action='store', dest="pastebin", default=None, 
        type="choice", choices=['failed', 'all'], 
        help="send failed|all info to Pocoo pastebin service.")

def pytest_configure(__multicall__, config):
    import tempfile
    __multicall__.execute()
    if config.option.pastebin == "all":
        config._pastebinfile = tempfile.TemporaryFile('w+')
        tr = config.pluginmanager.impname2plugin['terminalreporter']
        oldwrite = tr._tw.write 
        def tee_write(s, **kwargs):
            oldwrite(s, **kwargs)
            config._pastebinfile.write(str(s))
        tr._tw.write = tee_write 

def pytest_unconfigure(config): 
    if hasattr(config, '_pastebinfile'):
        config._pastebinfile.seek(0)
        sessionlog = config._pastebinfile.read()
        config._pastebinfile.close()
        del config._pastebinfile
        proxyid = getproxy().newPaste("python", sessionlog)
        pastebinurl = "%s%s" % (url.show, proxyid)
        sys.stderr.write("session-log: %s" % pastebinurl)
        tr = config.pluginmanager.impname2plugin['terminalreporter']
        del tr._tw.__dict__['write']
        
def getproxy():
    return py.std.xmlrpclib.ServerProxy(url.xmlrpc).pastes

def pytest_terminal_summary(terminalreporter):
    if terminalreporter.config.option.pastebin != "failed":
        return
    tr = terminalreporter
    if 'failed' in tr.stats:
        terminalreporter.write_sep("=", "Sending information to Paste Service")
        if tr.config.option.debug:
            terminalreporter.write_line("xmlrpcurl: %s" %(url.xmlrpc,))
        serverproxy = getproxy()
        for rep in terminalreporter.stats.get('failed'):
            try:
                msg = rep.longrepr.reprtraceback.reprentries[-1].reprfileloc
            except AttributeError:
                msg = tr._getfailureheadline(rep)
            tw = py.io.TerminalWriter(stringio=True)
            rep.toterminal(tw)
            s = tw.stringio.getvalue()
            assert len(s)
            proxyid = serverproxy.newPaste("python", s)
            pastebinurl = "%s%s" % (url.show, proxyid)
            tr.write_line("%s --> %s" %(msg, pastebinurl))

   
class TestPasting:
    def pytest_funcarg__pastebinlist(self, request):
        mp = request.getfuncargvalue("monkeypatch") 
        pastebinlist = []
        class MockProxy:
            def newPaste(self, language, code):
                pastebinlist.append((language, code))
        mp.setitem(globals(), 'getproxy', MockProxy) 
        return pastebinlist 

    def test_failed(self, testdir, pastebinlist):
        testpath = testdir.makepyfile("""
            import py
            def test_pass():
                pass
            def test_fail():
                assert 0
            def test_skip():
                py.test.skip("")
        """)
        reprec = testdir.inline_run(testpath, "--paste=failed")
        assert len(pastebinlist) == 1
        assert pastebinlist[0][0] == "python"
        s = pastebinlist[0][1]
        assert s.find("def test_fail") != -1
        assert reprec.countoutcomes() == [1,1,1]

    def test_all(self, testdir, pastebinlist):
        testpath = testdir.makepyfile("""
            import py
            def test_pass():
                pass
            def test_fail():
                assert 0
            def test_skip():
                py.test.skip("")
        """)
        reprec = testdir.inline_run(testpath, "--pastebin=all")
        assert reprec.countoutcomes() == [1,1,1]
        assert len(pastebinlist) == 1
        assert pastebinlist[0][0] == "python"
        s = pastebinlist[0][1]
        for x in 'test_fail test_skip skipped'.split():
            assert s.find(x), (s, x)
         
