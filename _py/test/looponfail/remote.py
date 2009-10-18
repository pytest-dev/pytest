"""
    LooponfailingSession and Helpers. 

    NOTE that one really has to avoid loading and depending on 
    application modules within the controlling process 
    (the one that starts repeatedly test processes)
    otherwise changes to source code can crash 
    the controlling process which should never happen. 
"""
import py
import sys
import execnet
from _py.test.session import Session
from _py.test.dist.mypickle import PickleChannel
from _py.test.looponfail import util

class LooponfailingSession(Session):
    def __init__(self, config):
        super(LooponfailingSession, self).__init__(config=config)
        self.rootdirs = [self.config.topdir] # xxx dist_rsync_roots? 
        self.statrecorder = util.StatRecorder(self.rootdirs) 
        self.remotecontrol = RemoteControl(self.config)
        self.out = py.io.TerminalWriter()

    def main(self, initialitems=None):
        try:
            self.loopstate = loopstate = LoopState(initialitems)
            self.remotecontrol.setup()
            while 1:
                self.loop_once(loopstate)
                if not loopstate.colitems and loopstate.wasfailing:
                    continue # the last failures passed, let's rerun all
                self.statrecorder.waitonchange(checkinterval=2.0) 
        except KeyboardInterrupt:
            print

    def loop_once(self, loopstate):
        colitems = loopstate.colitems
        loopstate.wasfailing = colitems and len(colitems)
        loopstate.colitems = self.remotecontrol.runsession(colitems or ())
        self.remotecontrol.setup()

class LoopState:
    def __init__(self, colitems=None):
        self.colitems = colitems

class RemoteControl(object):
    def __init__(self, config):
        self.config = config

    def trace(self, *args):
        if self.config.option.debug:
            msg = " ".join([str(x) for x in args])
            py.builtin.print_("RemoteControl:", msg)

    def initgateway(self):
        return execnet.PopenGateway()

    def setup(self, out=None):
        if out is None:
            out = py.io.TerminalWriter()
        if hasattr(self, 'gateway'):
            raise ValueError("already have gateway %r" % self.gateway)
        self.trace("setting up slave session")
        old = self.config.topdir.chdir()
        try:
            self.gateway = self.initgateway()
        finally:
            old.chdir()
        channel = self.gateway.remote_exec(source="""
            from _py.test.dist.mypickle import PickleChannel
            from _py.test.looponfail.remote import slave_runsession
            outchannel = channel.gateway.newchannel()
            channel.send(outchannel)
            channel = PickleChannel(channel)
            config, fullwidth, hasmarkup = channel.receive()
            import sys
            sys.stdout = sys.stderr = outchannel.makefile('w')
            slave_runsession(channel, config, fullwidth, hasmarkup) 
        """)
        remote_outchannel = channel.receive()
        def write(s):
            out._file.write(s)
            out._file.flush()
        remote_outchannel.setcallback(write)
        channel = self.channel = PickleChannel(channel)
        channel.send((self.config, out.fullwidth, out.hasmarkup))
        self.trace("set up of slave session complete")

    def ensure_teardown(self):
        if hasattr(self, 'channel'):
            if not self.channel.isclosed():
                self.trace("closing", self.channel)
                self.channel.close()
            del self.channel
        if hasattr(self, 'gateway'):
            self.trace("exiting", self.gateway)
            self.gateway.exit()
            del self.gateway

    def runsession(self, colitems=()):
        try:
            self.trace("sending", colitems)
            trails = colitems
            self.channel.send(trails)
            try:
                return self.channel.receive()
            except self.channel.RemoteError:
                e = sys.exc_info()[1]
                self.trace("ERROR", e)
                raise
        finally:
            self.ensure_teardown()

def slave_runsession(channel, config, fullwidth, hasmarkup):
    """ we run this on the other side. """
    if config.option.debug:
        def DEBUG(*args): 
            print(" ".join(map(str, args)))
    else:
        def DEBUG(*args): pass

    DEBUG("SLAVE: received configuration, using topdir:", config.topdir)
    #config.option.session = None
    config.option.looponfail = False 
    config.option.usepdb = False 
    trails = channel.receive()
    config.pluginmanager.do_configure(config)
    DEBUG("SLAVE: initsession()")
    session = config.initsession()
    # XXX configure the reporter object's terminal writer more directly
    # XXX and write a test for this remote-terminal setting logic 
    config.pytest_terminal_hasmarkup = hasmarkup
    config.pytest_terminal_fullwidth = fullwidth
    if trails:
        colitems = []
        for trail in trails:
            try:
                colitem = py.test.collect.Collector._fromtrail(trail, config)
            except AssertionError:  
                #XXX send info for "test disappeared" or so
                continue 
            colitems.append(colitem)
    else:
        colitems = None
    session.shouldclose = channel.isclosed 
   
    class Failures(list):
        def pytest_runtest_logreport(self, report):
            if report.failed:
                self.append(report)
        pytest_collectreport = pytest_runtest_logreport
        
    failreports = Failures()
    session.pluginmanager.register(failreports)

    DEBUG("SLAVE: starting session.main()")
    session.main(colitems)
    session.config.hook.pytest_looponfailinfo(
        failreports=list(failreports), 
        rootdirs=[config.topdir])
    channel.send([rep.getnode()._totrail() for rep in failreports])
