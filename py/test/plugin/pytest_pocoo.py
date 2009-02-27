"""
py.test plugin for sending testing failure information to paste.pocoo.org 
"""
import py

class url:
    base = "http://paste.pocoo.org"
    xmlrpc = base + "/xmlrpc/"
    show = base + "/show/"

class PocooPlugin(object):
    """ report URLs from sending test failures to the pocoo paste service. """

    def pytest_addoption(self, parser):
        parser.addoption('--pocoo-sendfailures', 
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
                serverproxy = self.getproxy()
                for ev in terminalreporter.stats.get('failed'):
                    tw = py.io.TerminalWriter(stringio=True)
                    ev.toterminal(tw)
                    s = tw.stringio.getvalue()
                    # XXX add failure summary 
                    assert len(s)
                    terminalreporter.write_line("newpaste() ...")
                    id = serverproxy.newPaste("python", s)
                    terminalreporter.write_line("%s%s\n" % (url.show, id))
                    break


def test_apicheck(plugintester):
    plugintester.apicheck(PocooPlugin)

pytest_plugins = 'pytest_monkeypatch', 
def test_toproxy(testdir, monkeypatch):
    testdir.makepyfile(conftest="pytest_plugins='pytest_pocoo',")
    testpath = testdir.makepyfile("""
        import py
        def test_pass():
            pass
        def test_fail():
            assert 0
        def test_skip():
            py.test.skip("")
    """)
    l = []
    class MockProxy:
        def newPaste(self, language, code):
            l.append((language, code))
          
    monkeypatch.setattr(PocooPlugin, 'getproxy', MockProxy) 
    result = testdir.inline_run(testpath, "--pocoo-sendfailures")
