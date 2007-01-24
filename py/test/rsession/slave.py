"""
Node code for slaves. 
"""

import py
from py.__.test.rsession.executor import RunExecutor, BoxExecutor, AsyncExecutor
from py.__.test.rsession.outcome import Outcome

class Info:
    pid = None

class SlaveNode(object):
    def __init__(self, rootcollector, executor=AsyncExecutor):
        self.rootcollector = rootcollector
        self.executor = executor

    def execute(self, itemspec):
        item = self.rootcollector.getitembynames(itemspec)
        #if isinstance(item, py.test.Function):
        #    ex = Executor(item.obj, setup=item.setup)
        #else:
        ex = self.executor(item)
        if self.executor is AsyncExecutor:
            cont, pid = ex.execute()
        else:
            # for tests only
            return ex.execute()
        Info.pid = pid
        return cont()

    def run(self, itemspec):
        #outcome = self.execute(itemspec)
        #return outcome.make_repr()
        outcome = self.execute(itemspec)
        if self.executor.wraps:
            return outcome
        else:
            return outcome.make_repr()

def slave_main(receive, send, path, info = None):
    import os
    assert os.path.exists(path) 
    path = os.path.abspath(path) 
    nodes = {}
    def getnode(item):
        node = nodes.get(item[0], None)
        if node is not None:
            return node
        col = py.test.collect.Directory(str(py.path.local(path).join(item[0])))
        node = nodes[item[0]] = SlaveNode(col)
        return node
    while 1:
        nextitem = receive()
        if nextitem is None:
            break
        try:
            node = getnode(nextitem)
            res = node.run(nextitem[1:])
        except py.test.Item.Skipped, s:
            send(Outcome(skipped=str(s)).make_repr())
        except:
            excinfo = py.code.ExceptionInfo()
            send(Outcome(excinfo=excinfo, is_critical=True).make_repr())
        else:
            from py.__.test.rsession.rsession import remote_options
            if not res[0] and not res[3] and remote_options.exitfirst:
                # we're finished, but need to eat what we can
                send(res)
                break
            send(res)
    
    while nextitem is not None:
        nextitem = receive()
    
def setup():
    def callback_gen(queue):
        from py.__.test.rsession.slave import Info
        def callback(item):
            if item == 42: # magic call-cleanup
                # XXX should kill a pid here
                if Info.pid:
                    os.kill(Info.pid, 15)
                sys.exit(0)
            queue.put(item)
        return callback

    import os, sys
    from Queue import Queue
    pkgdir = channel.receive()   # path is ready 
    options = channel.receive()  # options stuff, should be dictionary
    basedir = os.path.dirname(pkgdir)
    pkgname = os.path.basename(pkgdir)
    # setup defaults...
    sys.path.insert(0, basedir)
    import py
    options['we_are_remote'] = True
    from py.__.test.rsession.rsession import RemoteOptions
    from py.__.test.rsession.slave import Info
    Info.pid = 0
    from py.__.test.rsession import rsession
    rsession.remote_options = RemoteOptions(options)
    # XXX the following assumes that py lib is there, a bit
    # much of an assumtion
    if not rsession.remote_options.nomagic:
        py.magic.invoke(assertion=1)
    mod = __import__(pkgname)
    assert py.path.local(mod.__file__).dirpath() == py.path.local(pkgdir)
    from py.__.test.rsession.slave import slave_main
    queue = Queue()
    channel.setcallback(callback_gen(queue))
    slave_main(queue.get, channel.send, basedir)
    if not rsession.remote_options.nomagic:
        py.magic.revoke(assertion=1)
