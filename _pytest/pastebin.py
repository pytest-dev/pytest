""" submit failure or test session information to a pastebin service. """
import py, sys

class url:
    base = "http://bpaste.net"
    xmlrpc = base + "/xmlrpc/"
    show = base + "/show/"

def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting")
    group._addoption('--pastebin', metavar="mode",
        action='store', dest="pastebin", default=None,
        choices=['failed', 'all'],
        help="send failed|all info to bpaste.net pastebin service.")

def pytest_configure(__multicall__, config):
    import tempfile
    __multicall__.execute()
    if config.option.pastebin == "all":
        config._pastebinfile = tempfile.TemporaryFile('w+')
        tr = config.pluginmanager.getplugin('terminalreporter')
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
        sys.stderr.write("pastebin session-log: %s\n" % pastebinurl)
        tr = config.pluginmanager.getplugin('terminalreporter')
        del tr._tw.__dict__['write']

def getproxy():
    if sys.version_info < (3, 0):
        from xmlrpclib import ServerProxy
    else:
        from xmlrpc.client import ServerProxy
    return ServerProxy(url.xmlrpc).pastes

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
