"""
Node code for Master. 
"""
import py
from py.__.test.rsession.outcome import ReprOutcome
from py.__.test.rsession import repevent

class MasterNode(object):
    def __init__(self, channel, reporter):
        self.channel = channel
        self.reporter = reporter
        self.pending = []
        channel.setcallback(self._callback)
       
    def _callback(self, outcome):
        item = self.pending.pop()
        self.receive_result(outcome, item)

    def receive_result(self, outcomestring, item):
        repr_outcome = ReprOutcome(outcomestring)
        # send finish report
        self.reporter(repevent.ReceivedItemOutcome(
                        self.channel, item, repr_outcome))

    def send(self, item):
        try:
            if item is StopIteration:
                self.channel.send(42)
            else:
                self.pending.insert(0, item)
            #itemspec = item.listnames()[1:]
                self.channel.send(item._get_collector_trail())
                # send start report
                self.reporter(repevent.SendItem(self.channel, item))
        except IOError:
            print "Sending error, channel IOError"
            print self.channel._getremoteerror()
            # XXX: this should go as soon as we'll have proper detection
            #      of hanging nodes and such
            raise

def itemgen(colitems, reporter, keyword, reporterror):
    def rep(x):
        reporterror(reporter, x)
    for x in colitems:
        for y in x._tryiter(reporterror=rep, keyword=keyword):
            yield y

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

