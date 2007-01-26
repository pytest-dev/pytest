"""
Node code for Master. 
"""
import py
from py.__.test.rsession.outcome import ReprOutcome
from py.__.test.rsession import report

class MasterNode(object):
    def __init__(self, channel, reporter, done_dict):
        self.channel = channel
        self.reporter = reporter
        
        def callback(outcome):
            item = self.pending.pop()
            if not item in done_dict:
                self.receive_result(outcome, item)
                done_dict[item] = True
        channel.setcallback(callback)
        self.pending = []

    def receive_result(self, outcomestring, item):
        repr_outcome = ReprOutcome(outcomestring)
        # send finish report
        self.reporter(report.ReceivedItemOutcome(
                        self.channel, item, repr_outcome))

    def send(self, item):
        if item is StopIteration:
            self.channel.send(42)
        else:
            self.pending.insert(0, item)
            #itemspec = item.listnames()[1:]
            self.channel.send(item.config.get_collector_trail(item))
            # send start report
            self.reporter(report.SendItem(self.channel, item))

def itemgen(colitems, reporter, keyword, reporterror):
    for x in colitems:
        for y in x.tryiter(reporterror = lambda x: reporterror(reporter, x), keyword = keyword):
            yield y

def randomgen(items, done_dict):
    """ Generator, which randomly gets all the tests from items as long
    as they're not in done_dict
    """
    import random
    while items:
        values = items.keys()
        item = values[int(random.random()*len(values))]
        if item in done_dict:
            del items[item]
        else:
            yield item

def dispatch_loop(masternodes, itemgenerator, shouldstop, 
                  waiter = lambda: py.std.time.sleep(0.1),
                  max_tasks_per_node=None):
    if not max_tasks_per_node:
        max_tasks_per_node = py.test.config.getvalue("dist_taskspernode")
    all_tests = {}
    while 1:
        try:
            for node in masternodes:
                if len(node.pending) < max_tasks_per_node:
                    item = itemgenerator.next()
                    all_tests[item] = True
                    if shouldstop():
                        for _node in masternodes:
                            _node.send(StopIteration) # magic connector
                        return None
                    node.send(item)
        except StopIteration:
            break
        waiter()
    return all_tests

def setup_slave(gateway, pkgpath, config):
    from py.__.test.rsession import slave
    import os
    ch = gateway.remote_exec(str(py.code.Source(slave.setup, "setup()")))
    #if hasattr(gateway, 'sshaddress'):
    #    assert not os.path.isabs(pkgpath)
    ch.send(str(pkgpath))
    ch.send(config.make_repr(defaultconftestnames))
    return ch

defaultconftestnames = ['dist_nicelevel']
