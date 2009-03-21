"""
py.test plugin for sending testing failure information to paste.pocoo.org 
"""
import py

class url:
    base = "http://paste.pocoo.org"
    xmlrpc = base + "/xmlrpc/"
    show = base + "/show/"

class PocooPlugin:
    """ report URLs from sending test failures to the pocoo paste service. """

    def pytest_addoption(self, parser):
        parser.addoption('-P', '--pocoo-sendfailures', 
            action='store_true', dest="pocoo_sendfailures", 
            help="send failures to %s" %(url.base,))

    def getproxy(self):
        return py.std.xmlrpclib.ServerProxy(url.xmlrpc).pastes

    def pytest_terminal_summary(self, terminalreporter):
        if terminalreporter.config.option.pocoo_sendfailures:
            tr = terminalreporter
            if 'failed' in tr.stats and tr.config.option.tbstyle != "no":
                terminalreporter.write_sep("=", "Sending failures to %s" %(url.base,))
                terminalreporter.write_line("xmlrpcurl: %s" %(url.xmlrpc,))
                print self.__class__.getproxy
                print self.__class__, id(self.__class__)
                serverproxy = self.getproxy()
                for ev in terminalreporter.stats.get('failed'):
                    tw = py.io.TerminalWriter(stringio=True)
                    ev.toterminal(tw)
                    s = tw.stringio.getvalue()
                    # XXX add failure summary 
                    assert len(s)
                    terminalreporter.write_line("newpaste() ...")
                    proxyid = serverproxy.newPaste("python", s)
                    terminalreporter.write_line("%s%s\n" % (url.show, proxyid))
                    break


def test_apicheck(plugintester):
    plugintester.apicheck(PocooPlugin)

def test_toproxy(testdir, monkeypatch):
    l = []
    class MockProxy:
        def newPaste(self, language, code):
            l.append((language, code))
    monkeypatch.setattr(PocooPlugin, 'getproxy', MockProxy) 
    testdir.plugins.insert(0, PocooPlugin())
    testdir.chdir()
    testpath = testdir.makepyfile("""
        import py
        def test_pass():
            pass
        def test_fail():
            assert 0
        def test_skip():
            py.test.skip("")
    """)
    evrec = testdir.inline_run(testpath, "-P")
    assert len(l) == 1
    assert l[0][0] == "python"
    s = l[0][1]
    assert s.find("def test_fail") != -1
    assert evrec.countoutcomes() == [1,1,1]
     
