import py
import sys
from py.__.test.outcome import Outcome, Failed, Passed, Skipped
from py.__.test.reporter import choose_reporter, TestReporter
from py.__.test import repevent
from py.__.test.outcome import SerializableOutcome, ReprOutcome
from py.__.test.reporter import LocalReporter
from py.__.test.executor import RunExecutor, BoxExecutor

""" The session implementation - reporter version:

* itemgen is responsible for iterating and telling reporter
  about skipped and failed iterations (this is for collectors only),
  this should be probably moved to session (for uniformity)
* session gets items which needs to be executed one after another
  and tells reporter about that
"""

try:
    GeneratorExit
except NameError:
    GeneratorExit = StopIteration # I think

def itemgen(session, colitems, reporter, keyword=None):
    stopitems = py.test.collect.Item # XXX should be generator here as well
    while 1:
        if not colitems:
            break
        next = colitems.pop(0)
        if reporter: 
            reporter(repevent.ItemStart(next))

        if isinstance(next, stopitems):
            try:
                next._skipbykeyword(keyword)
                if session and session.config.option.keyword_oneshot:
                    keyword = None
                yield next
            except Skipped:
                excinfo = py.code.ExceptionInfo()
                reporter(repevent.SkippedTryiter(excinfo, next))
        else:
            try:
                cols = [next.join(x) for x in next.run()]
                for x in itemgen(session, cols, reporter, keyword):
                    yield x
            except (KeyboardInterrupt, SystemExit, GeneratorExit):
                raise
            except:
                excinfo = py.code.ExceptionInfo()
                if excinfo.type is Skipped:
                    reporter(repevent.SkippedTryiter(excinfo, next))
                else:
                    reporter(repevent.FailedTryiter(excinfo, next))
        if reporter: 
            reporter(repevent.ItemFinish(next))

class AbstractSession(object): 
    """ An abstract session executes collectors/items through a runner. 
    """
    def __init__(self, config):
        self.config = config
        self._keyword = config.option.keyword

    def fixoptions(self):
        """ check, fix and determine conflicting options. """
        option = self.config.option 
        if option.runbrowser and not option.startserver:
            #print "--runbrowser implies --startserver"
            option.startserver = True
        if self.config.getvalue("dist_boxed") and option.dist:
            option.boxed = True
        # conflicting options
        if option.looponfailing and option.usepdb:
            raise ValueError, "--looponfailing together with --pdb not supported."
        if option.looponfailing and option.dist:
            raise ValueError, "--looponfailing together with --dist not supported."
        if option.executable and option.usepdb:
            raise ValueError, "--exec together with --pdb not supported."

        if option.keyword_oneshot and not option.keyword:
            raise ValueError, "--keyword-oneshot makes sense only when --keyword is supplied"

    def init_reporter(self, reporter, config, hosts):
        if reporter is None:
            reporter = choose_reporter(self.reporterclass, config)\
                       (config, hosts)
        else:
            reporter = TestReporter(reporter)
        checkfun = lambda : self.config.option.exitfirst and \
                            reporter.was_failure()
        return reporter, checkfun

class Session(AbstractSession):
    """
        A Session gets test Items from Collectors, executes the
        Items and sends the Outcome to the Reporter.
    """
    reporterclass = LocalReporter
    
    def shouldclose(self): 
        return False

    def header(self, colitems):
        """ setup any neccessary resources ahead of the test run. """
        self.reporter(repevent.TestStarted(None, self.config,
                                            None))
        if not self.config.option.nomagic:
            py.magic.invoke(assertion=1)

    def footer(self, colitems):
        """ teardown any resources after a test run. """ 
        py.test.collect.Function._state.teardown_all()
        if not self.config.option.nomagic:
            py.magic.revoke(assertion=1)
        self.reporter(repevent.TestFinished())
    
    def main(self, reporter=None):
        """ main loop for running tests. """
        config = self.config
        self.reporter, shouldstop = self.init_reporter(reporter, config, None)

        colitems = self.config.getcolitems()
        self.header(colitems)
        keyword = self.config.option.keyword
        reporter = self.reporter
        itemgenerator = itemgen(self, colitems, reporter, keyword)
        failures = []
        try:
            while 1:
                try:
                    item = itemgenerator.next()
                    if shouldstop():
                        return
                    outcome = self.run(item)
                    if outcome is not None: 
                        if not outcome.passed and not outcome.skipped: 
                            failures.append((item, outcome))
                    reporter(repevent.ReceivedItemOutcome(None, item, outcome))
                except StopIteration:
                    break
        finally:
            self.footer(colitems)
        return failures 
        return self.getitemoutcomepairs(Failed)

    def run(self, item):
        if not self.config.option.boxed:
            executor = RunExecutor(item, self.config.option.usepdb,
                                   self.reporter, self.config)
            return ReprOutcome(executor.execute().make_repr())
        else:
            executor = BoxExecutor(item, self.config.option.usepdb,
                                   self.reporter, self.config)
            return ReprOutcome(executor.execute())

class Exit(Exception):
    """ for immediate program exits without tracebacks and reporter/summary. """
    def __init__(self, msg="unknown reason", item=None):
        self.msg = msg 
        Exception.__init__(self, msg)

def exit(msg, item=None): 
    raise Exit(msg=msg, item=item)

