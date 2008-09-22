"""
    LooponfailingSession and Helpers. 

    NOTE that one really has to avoid loading and depending on 
    application modules within the controlling process 
    (the one that starts repeatedly test processes)
    otherwise changes to source code can crash 
    the controlling process which should never happen. 
"""

from __future__ import generators
import py
from py.__.test.session import Session
from py.__.test.outcome import Failed, Passed, Skipped
from py.__.test.dsession.mypickle import PickleChannel
from py.__.test.report.terminal import TerminalReporter
from py.__.test import event
from py.__.test.looponfail import util

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
                    continue # rerun immediately
                self.statrecorder.waitonchange(checkinterval=2.0) 
        except KeyboardInterrupt:
            print
            pass

    def loop_once(self, loopstate):
        colitems = loopstate.colitems
        loopstate.wasfailing = colitems and len(colitems)
        loopstate.colitems = self.remotecontrol.runsession(colitems or ())
        #ev = event.LooponfailingInfo(loopstate.failreports, self.rootdirs)
        self.remotecontrol.setup()

class LoopState:
    def __init__(self, colitems=None):
        self.colitems = colitems

class RemoteControl(object):
    def __init__(self, config):
        self.config = config
        self._setexecutable()

    def _setexecutable(self):
        # XXX --exec logic should go to DSession 
        name = self.config.option.executable
        if name is None:
            executable = py.std.sys.executable 
        else:
            executable = py.path.local.sysfind(name)
            assert executable is not None, executable 
        self.executable = executable 

    def trace(self, *args):
        if self.config.option.debug:
            msg = " ".join([str(x) for x in args])
            print "RemoteControl:", msg 

    def setup(self, out=None):
        if hasattr(self, 'gateway'):
            raise ValueError("already have gateway %r" % self.gateway)
        if out is None:
            out = py.io.TerminalWriter()
        from py.__.test.dsession import masterslave
        self.trace("setting up slave session")
        self.gateway = py.execnet.PopenGateway(self.executable)
        channel = self.gateway.remote_exec(source="""
            from py.__.test.dsession.mypickle import PickleChannel
            channel = PickleChannel(channel)
            from py.__.test.looponfail.remote import slave_runsession
            from py.__.test.dsession import masterslave
            config = masterslave.receive_and_send_pickled_config(channel)
            width, hasmarkup = channel.receive()
            slave_runsession(channel, config, width, hasmarkup) 
        """, stdout=out, stderr=out)
        channel = PickleChannel(channel)
        masterslave.send_and_receive_pickled_config(
            channel, self.config, remote_topdir=self.config.topdir)
        channel.send((out.fullwidth, out.hasmarkup))
        self.trace("set up of slave session complete")
        self.channel = channel

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
            except self.channel.RemoteError, e:
                self.trace("ERROR", e)
                raise
        finally:
            self.ensure_teardown()

def slave_runsession(channel, config, width, hasmarkup):
    """ we run this on the other side. """
    if config.option.debug:
        def DEBUG(*args): 
            print " ".join(map(str, args))
    else:
        def DEBUG(*args): pass

    DEBUG("SLAVE: received configuration, using topdir:", config.topdir)
    #config.option.session = None
    config.option.looponfailing = False 
    config.option.usepdb = False 
    config.option.executable = None
    trails = channel.receive()
        
    DEBUG("SLAVE: initsession()")
    session = config.initsession()
    session.reporter._tw.hasmarkup = hasmarkup
    session.reporter._tw.fullwidth = width
    if trails:
        colitems = []
        for trail in trails:
            try:
                colitem = py.test.collect.Collector._fromtrail(trail, config)
            except AssertionError, e:  
                #XXX session.bus.notify of "test disappeared"
                continue 
            colitems.append(colitem)
    else:
        colitems = None
    session.shouldclose = channel.isclosed 
    #def sendevent(ev):
    #    channel.send(ev)
    #session.bus.subscribe(sendevent)
    failreports = []
    def recordfailures(ev):
        if isinstance(ev, event.BaseReport): 
            if ev.failed:
                failreports.append(ev)
    session.bus.subscribe(recordfailures)

    DEBUG("SLAVE: starting session.main()")
    session.main(colitems)
    session.bus.unsubscribe(recordfailures)
    ev = event.LooponfailingInfo(failreports, [config.topdir])
    session.bus.notify(ev)
    channel.send([x.colitem._totrail() for x in failreports if x.failed])
