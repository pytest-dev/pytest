"""
    Manage setup, running and local representation of remote nodes/processes. 
"""
import py
from py.__.test import event
from py.__.test.dsession.mypickle import PickleChannel

class MasterNode(object):
    ENDMARK = -1

    def __init__(self, host, gateway, config, putevent):
        self.host = host 
        self.config = config 
        self.putevent = putevent 
        self.channel = install_slave(host, gateway, config)
        self.channel.setcallback(self.callback, endmarker=self.ENDMARK)
        self._down = False

    def notify(self, eventname, *args, **kwargs):
        self.putevent((eventname, args, kwargs))
      
    def callback(self, eventcall):
        """ this gets called for each object we receive from 
            the other side and if the channel closes. 

            Note that channel callbacks run in the receiver
            thread of execnet gateways - we need to 
            avoid raising exceptions or doing heavy work.
        """
        try:
            if eventcall == self.ENDMARK:
                err = self.channel._getremoteerror()
                if not self._down:
                    if not err:
                        err = "TERMINATED"
                    self.notify("testnodedown", event.HostDown(self.host, err))
                return
            elif eventcall is None:
                self._down = True
                self.notify("testnodedown", event.HostDown(self.host, None))
                return 
        except KeyboardInterrupt:
            raise 
        except:
            excinfo = py.code.ExceptionInfo()
            print "!" * 20, excinfo
            self.notify("internalerror", event.InternalException(excinfo))
        else:
            # XXX we need to have the proper event name 
            eventname, args, kwargs = eventcall 
            self.notify(eventname, *args, **kwargs)

    def send(self, item):
        assert item is not None
        self.channel.send(item)

    def sendlist(self, itemlist):
        self.channel.send(itemlist)

    def shutdown(self):
        self.channel.send(None)

# setting up slave code 
def install_slave(host, gateway, config):
    channel = gateway.remote_exec(source="""
        from py.__.test.dsession.mypickle import PickleChannel
        from py.__.test.dsession.masterslave import SlaveNode
        channel = PickleChannel(channel)
        slavenode = SlaveNode(channel)
        slavenode.run()
    """)
    channel = PickleChannel(channel)
    basetemp = None
    if host.popen:
        popenbase = config.ensuretemp("popen")
        basetemp = py.path.local.make_numbered_dir(prefix="slave-", 
            keep=0, rootdir=popenbase)
        basetemp = str(basetemp)
    channel.send((host, config, basetemp))
    return channel

class SlaveNode(object):
    def __init__(self, channel):
        self.channel = channel

    def __repr__(self):
        return "<%s channel=%s>" %(self.__class__.__name__, self.channel)

    def sendevent(self, eventname, *args, **kwargs):
        self.channel.send((eventname, args, kwargs))

    def run(self):
        channel = self.channel
        host, self.config, basetemp = channel.receive()
        if basetemp:
            self.config.basetemp = py.path.local(basetemp)
        self.config.pytestplugins.do_configure(self.config)
        self.sendevent("testnodeready", maketestnodeready(host))
        try:
            while 1:
                task = channel.receive()
                self.config.bus.notify("masterslave_receivedtask", task)
                if task is None: # shutdown
                    self.channel.send(None)
                    break
                if isinstance(task, list):
                    for item in task:
                        self.runtest(item)
                else:
                    self.runtest(task)
        except KeyboardInterrupt:
            raise
        except:
            self.sendevent("internalerror", event.InternalException())
            raise

    def runtest(self, item):
        runner = item._getrunner()
        testrep = runner(item)
        self.sendevent("itemtestreport", testrep)


def maketestnodeready(host="INPROCESS"):
    import sys
    platinfo = {}
    for name in 'platform', 'executable', 'version_info':
        platinfo["sys."+name] = getattr(sys, name)
    return event.HostUp(host, platinfo)
