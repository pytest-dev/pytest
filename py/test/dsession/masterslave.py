"""
    Manage setup, running and local representation of remote nodes/processes. 
"""
import py
from py.__.test import event
from py.__.test.dsession.mypickle import PickleChannel

class MasterNode(object):
    ENDMARK = -1

    def __init__(self, host, config, notify):
        self.host = host 
        self.config = config 
        self.notify = notify 
        self.channel = install_slave(host, config)
        self.channel.setcallback(self.callback, endmarker=self.ENDMARK)
        self._down = False
      
    def callback(self, ev):
        """ this gets called for each item we receive from 
            the other side and if the channel closes. 

            Note that the callback runs in the receiver
            thread of execnet gateways - we need to 
            avoid raising exceptions or doing heavy work.
        """
        try:
            if ev == self.ENDMARK:
                err = self.channel._getremoteerror()
                if not self._down:
                    if not err:
                        err = "TERMINATED"
                    self.notify(event.HostDown(self.host, err))
                return
            if ev is None:
                self._down = True
                self.notify(event.HostDown(self.host, None))
                return 
        except KeyboardInterrupt:
            raise 
        except:
            excinfo = py.code.ExceptionInfo()
            print "!" * 20, excinfo
            ev = event.InternalException(excinfo)
        self.notify(ev) 

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
        masterslave.setup_at_slave_side(channel, config)
    """)
    channel = PickleChannel(channel)
    remote_topdir = host.gw_remotepath 
    if remote_topdir is None:
        assert host.inplacelocal
        remote_topdir = config.topdir
    send_and_receive_pickled_config(channel, config, remote_topdir)
    channel.send(host)
    return channel

def setup_at_slave_side(channel, config):
    # our current dir is the topdir
    # XXX what about neccessary PYTHONPATHs? 
    import os
    if hasattr(os, 'nice'):
        nice_level = config.getvalue('dist_nicelevel')
        os.nice(nice_level) 
    from py.__.test.dsession.hostmanage import makehostup
    host = channel.receive()
    channel.send(makehostup(host))
    while 1:
        task = channel.receive()
        if task is None: # shutdown
            channel.send(None)
            break
        if isinstance(task, list):
            for item in task:
                runtest(channel, item)
        else:
            runtest(channel, task)

def runtest(channel, item):
    runner = item._getrunner()
    testrep = runner(item)
    channel.send(testrep)
