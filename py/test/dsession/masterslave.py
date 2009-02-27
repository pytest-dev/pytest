"""
    Manage setup, running and local representation of remote nodes/processes. 
"""
import py
from py.__.test import event
from py.__.test.dsession.mypickle import PickleChannel

class MasterNode(object):
    ENDMARK = -1

    def __init__(self, host, config, putevent):
        self.host = host 
        self.config = config 
        self.putevent = putevent 
        self.channel = install_slave(host, config)
        self.channel.setcallback(self.callback, endmarker=self.ENDMARK)
        self._down = False

    def notify(self, eventname, *args, **kwargs):
        self.putevent((eventname, args, kwargs))
      
    def callback(self, eventcall):
        """ this gets called for each object we receive from 
            the other side and if the channel closes. 

            Note that the callback runs in the receiver
            thread of execnet gateways - we need to 
            avoid raising exceptions or doing heavy work.
        """
        try:
            if eventcall == self.ENDMARK:
                err = self.channel._getremoteerror()
                if not self._down:
                    if not err:
                        err = "TERMINATED"
                    self.notify("hostdown", event.HostDown(self.host, err))
                return
            elif eventcall is None:
                self._down = True
                self.notify("hostdown", event.HostDown(self.host, None))
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

#
# a config needs to be available on the other side for options
# and for reconstructing collection trees (topdir, conftest access)
#

def send_and_receive_pickled_config(channel, config, remote_topdir):
    channel.send((config, remote_topdir))
    backconfig = channel.receive()
    assert config is backconfig  # ImmutablePickling :) 
    return backconfig

def receive_and_send_pickled_config(channel):
    config,topdir = channel.receive()
    config._initafterpickle(topdir)
    channel.send(config)
    return config

# setting up slave code 
def install_slave(host, config):
    channel = host.gw.remote_exec(source="""
        from py.__.test.dsession.mypickle import PickleChannel
        channel = PickleChannel(channel)
        from py.__.test.dsession import masterslave
        config = masterslave.receive_and_send_pickled_config(channel)
        slavenode = masterslave.SlaveNode(channel, config)
        slavenode.run()
    """)
    channel = PickleChannel(channel)
    remote_topdir = host.gw_remotepath 
    if remote_topdir is None:
        assert host.inplacelocal
        remote_topdir = config.topdir
    send_and_receive_pickled_config(channel, config, remote_topdir)
    channel.send(host)
    return channel

class SlaveNode(object):
    def __init__(self, channel, config):
        self.channel = channel
        self.config = config
        import os
        if hasattr(os, 'nice'):
            nice_level = config.getvalue('dist_nicelevel')
            os.nice(nice_level) 

    def __repr__(self):
        host = getattr(self, 'host', '<uninitialized>')
        return "<%s host=%s>" %(self.__class__.__name__, host)

    def sendevent(self, eventname, *args, **kwargs):
        self.channel.send((eventname, args, kwargs))

    def run(self):
        self.config.pytestplugins.configure(self.config)
        from py.__.test.dsession.hostmanage import makehostup
        channel = self.channel
        self.host = host = channel.receive()
        self.sendevent("hostup", makehostup(host))
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
