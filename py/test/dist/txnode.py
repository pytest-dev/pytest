"""
    Manage setup, running and local representation of remote nodes/processes. 
"""
import py
from py.__.test.dist.mypickle import PickleChannel

class TXNode(object):
    """ Represents a Test Execution environment in the controlling process. 
        - sets up a slave node through an execnet gateway 
        - manages sending of test-items and receival of results and events
        - creates events when the remote side crashes 
    """
    ENDMARK = -1

    def __init__(self, gateway, config, putevent, slaveready=None):
        self.config = config 
        self.putevent = putevent 
        self.gateway = gateway
        self.channel = install_slave(gateway, config)
        self._sendslaveready = slaveready
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
                        err = "Not properly terminated"
                    self.notify("testnodedown", self, err)
                    self._down = True
                return
            eventname, args, kwargs = eventcall 
            if eventname == "slaveready":
                if self._sendslaveready:
                    self._sendslaveready(self)
                self.notify("testnodeready", self)
            elif eventname == "slavefinished":
                self._down = True
                self.notify("testnodedown", self, None)
            elif eventname == "itemtestreport":
                rep = args[0]
                rep.node = self
                self.notify("itemtestreport", rep)
            else:
                self.notify(eventname, *args, **kwargs)
        except KeyboardInterrupt: 
            # should not land in receiver-thread
            raise 
        except:
            excinfo = py.code.ExceptionInfo()
            print "!" * 20, excinfo
            self.config.pytestplugins.notify_exception(excinfo)

    def send(self, item):
        assert item is not None
        self.channel.send(item)

    def sendlist(self, itemlist):
        self.channel.send(itemlist)

    def shutdown(self):
        self.channel.send(None)

# setting up slave code 
def install_slave(gateway, config):
    channel = gateway.remote_exec(source="""
        import os, sys 
        sys.path.insert(0, os.getcwd()) 
        from py.__.test.dist.mypickle import PickleChannel
        from py.__.test.dist.txnode import SlaveNode
        channel = PickleChannel(channel)
        slavenode = SlaveNode(channel)
        slavenode.run()
    """)
    channel = PickleChannel(channel)
    basetemp = None
    if gateway.spec.popen:
        popenbase = config.ensuretemp("popen")
        basetemp = py.path.local.make_numbered_dir(prefix="slave-", 
            keep=0, rootdir=popenbase)
        basetemp = str(basetemp)
    channel.send((config, basetemp))
    return channel

class SlaveNode(object):
    def __init__(self, channel):
        self.channel = channel

    def __repr__(self):
        return "<%s channel=%s>" %(self.__class__.__name__, self.channel)

    def sendevent(self, eventname, *args, **kwargs):
        self.channel.send((eventname, args, kwargs))

    def pyevent__itemtestreport(self, rep):
        self.sendevent("itemtestreport", rep)

    def run(self):
        channel = self.channel
        self.config, basetemp = channel.receive()
        if basetemp:
            self.config.basetemp = py.path.local(basetemp)
        self.config.pytestplugins.do_configure(self.config)
        self.config.pytestplugins.register(self)
        self.sendevent("slaveready")
        try:
            while 1:
                task = channel.receive()
                if task is None: 
                    self.sendevent("slavefinished")
                    break
                if isinstance(task, list):
                    for item in task:
                        item.config.pytestplugins.do_itemrun(item)
                else:
                    task.config.pytestplugins.do_itemrun(item=task)
        except KeyboardInterrupt:
            raise
        except:
            er = py.code.ExceptionInfo().getrepr(funcargs=True, showlocals=True)
            self.sendevent("internalerror", excrepr=er)
            raise
