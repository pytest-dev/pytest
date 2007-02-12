"""
Node code for slaves. 
"""

import py
from py.__.test.rsession.executor import RunExecutor, BoxExecutor, AsyncExecutor
from py.__.test.rsession.outcome import Outcome
from py.__.test.outcome import Skipped
import thread
import os

class SlaveNode(object):
    def __init__(self, config, executor):
        #self.rootcollector = rootcollector
        self.config = config
        self.executor = executor

    def execute(self, itemspec):
        item = self.config._getcollector(itemspec)
        ex = self.executor(item, config=self.config)
        return ex.execute()

    def run(self, itemspec):
        #outcome = self.execute(itemspec)
        #return outcome.make_repr()
        outcome = self.execute(itemspec)
        if self.executor.wraps:
            return outcome
        else:
            return outcome.make_repr(self.config.option.tbstyle)

def slave_main(receive, send, path, config):
    import os
    assert os.path.exists(path) 
    path = os.path.abspath(path) 
    nodes = {}
    def getnode(item):
        node = nodes.get(item[0], None)
        if node is not None:
            return node
        col = py.test.collect.Directory(str(py.path.local(path).join(item[0])))
        if config.option.boxed:
            executor = BoxExecutor
        else:
            executor = RunExecutor
        node = nodes[item[0]] = SlaveNode(config, executor)
        return node
    while 1:
        nextitem = receive()
        if nextitem is None:
            break
        try:
            node = getnode(nextitem)
            res = node.run(nextitem)
        except Skipped, s:
            send(Outcome(skipped=str(s)).make_repr())
        except:
            excinfo = py.code.ExceptionInfo()
            send(Outcome(excinfo=excinfo, is_critical=True).make_repr())
        else:
            if not res[0] and not res[3] and config.option.exitfirst:
                # we're finished, but need to eat what we can
                send(res)
                break
            send(res)
    
    while nextitem is not None:
        nextitem = receive()

defaultconftestnames = ['dist_nicelevel']
def setup_slave(host, config): 
    channel = host.gw.remote_exec(str(py.code.Source(setup, "setup()")))
    configrepr = config._makerepr(defaultconftestnames)
    #print "sending configrepr", configrepr
    topdir = host.gw_remotepath 
    if topdir is None:
        assert host.inplacelocal
        topdir = config.topdir
    channel.send(str(topdir))
    channel.send(configrepr) 
    return channel

def setup():
    # our current dir is the topdir
    import os, sys
    basedir = channel.receive()
    config_repr = channel.receive()
    # setup defaults...
    sys.path.insert(0, basedir)
    import py
    config = py.test.config
    assert not config._initialized 
    config._initdirect(basedir, config_repr)
    if hasattr(os, 'nice'):
        nice_level = config.getvalue('dist_nicelevel')
        os.nice(nice_level) 
    if not config.option.nomagic:
        py.magic.invoke(assertion=1)
    from py.__.test.rsession.slave import slave_main
    slave_main(channel.receive, channel.send, basedir, config)
    if not config.option.nomagic:
        py.magic.revoke(assertion=1)
    channel.close()
