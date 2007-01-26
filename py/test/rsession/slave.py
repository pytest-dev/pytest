"""
Node code for slaves. 
"""

import py
from py.__.test.rsession.executor import RunExecutor, BoxExecutor, AsyncExecutor
from py.__.test.rsession.outcome import Outcome
import thread
import os

class PidInfo(object):
    """ Pure container class to store information of actually running
    pid
    """
    def __init__(self):
        self.pid = 0
        self.lock = thread.allocate_lock()

    def set_pid(self, pid):
        self.lock.acquire()
        try:
            self.pid = pid
        finally:
            self.lock.release()

    def kill(self):
        self.lock.acquire()
        try:
            if self.pid:
                os.kill(self.pid, 15)
                self.pid = 0
        finally:
            self.lock.release()

    def waitandclear(self, pid, num):
        """ This is an obscure hack to keep locking properly, adhere to posix semantics
        and try to clean it as much as possible, not clean at all
        """
        self.lock.acquire()
        try:
            retval = os.waitpid(self.pid, 0)
            self.pid = 0
            return retval
        finally:
            self.lock.release()

class SlaveNode(object):
    def __init__(self, config, pidinfo, executor=AsyncExecutor):
        #self.rootcollector = rootcollector
        self.config = config
        self.executor = executor
        self.pidinfo = pidinfo

    def execute(self, itemspec):
        #item = self.rootcollector.getitembynames(itemspec)
        item = self.config._getcollector(itemspec)
        #if isinstance(item, py.test.Function):
        #    ex = Executor(item.obj, setup=item.setup)
        #else:
        ex = self.executor(item, config=self.config)
        if self.executor is AsyncExecutor:
            cont, pid = ex.execute()
            self.pidinfo.set_pid(pid)
        else:
            # for tests only
            return ex.execute()
        return cont(self.pidinfo.waitandclear)

    def run(self, itemspec):
        #outcome = self.execute(itemspec)
        #return outcome.make_repr()
        outcome = self.execute(itemspec)
        if self.executor.wraps:
            return outcome
        else:
            return outcome.make_repr(self.config.option.tbstyle)

def slave_main(receive, send, path, config, pidinfo):
    import os
    assert os.path.exists(path) 
    path = os.path.abspath(path) 
    nodes = {}
    def getnode(item):
        node = nodes.get(item[0], None)
        if node is not None:
            return node
        col = py.test.collect.Directory(str(py.path.local(path).join(item[0])))
        node = nodes[item[0]] = SlaveNode(config, pidinfo)
        return node
    while 1:
        nextitem = receive()
        if nextitem is None:
            break
        try:
            node = getnode(nextitem)
            res = node.run(nextitem)
        except py.test.Item.Skipped, s:
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

def setup():
    def callback_gen(channel, queue, info):
        def callback(item):
            if item == 42: # magic call-cleanup
                # XXX should kill a pid here
                info.kill()
                channel.close()
                sys.exit(0)
            queue.put(item)
        return callback

    import os, sys
    basedir = channel.receive()   # path is ready 
    config_repr = channel.receive()
    # setup defaults...
    sys.path.insert(0, basedir)
    import py
    config = py.test.config
    if config._initialized:
        config = config._reparse([basedir])
        config.merge_repr(config_repr)
    else:
        config.initdirect(basedir, config_repr)
    if not config.option.nomagic:
        py.magic.invoke(assertion=1)
    from py.__.test.rsession.slave import slave_main, PidInfo
    queue = py.std.Queue.Queue()
    pidinfo = PidInfo()
    channel.setcallback(callback_gen(channel, queue, pidinfo))
    slave_main(queue.get, channel.send, basedir, config, pidinfo)
    if not config.option.nomagic:
        py.magic.revoke(assertion=1)
    channel.close()
