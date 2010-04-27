""" basic test session implementation. 

* drives collection of tests 
* triggers executions of tests   
* produces events used by reporting 
"""

import py

# exitcodes for the command line
EXIT_OK = 0
EXIT_TESTSFAILED = 1
EXIT_INTERRUPTED = 2
EXIT_INTERNALERROR = 3
EXIT_NOHOSTS = 4

# imports used for genitems()
Item = py.test.collect.Item
Collector = py.test.collect.Collector

class Session(object): 
    nodeid = ""
    def __init__(self, config):
        self.config = config
        self.pluginmanager = config.pluginmanager # shortcut 
        self.pluginmanager.register(self)
        self._testsfailed = False
        self._nomatch = False
        self.shouldstop = False

    def genitems(self, colitems, keywordexpr=None):
        """ yield Items from iterating over the given colitems. """
        if colitems:
            colitems = list(colitems)
        while colitems: 
            next = colitems.pop(0)
            if isinstance(next, (tuple, list)):
                colitems[:] = list(next) + colitems 
                continue
            assert self.pluginmanager is next.config.pluginmanager
            if isinstance(next, Item):
                remaining = self.filteritems([next])
                if remaining:
                    self.config.hook.pytest_itemstart(item=next)
                    yield next 
            else:
                assert isinstance(next, Collector)
                self.config.hook.pytest_collectstart(collector=next)
                rep = self.config.hook.pytest_make_collect_report(collector=next)
                if rep.passed:
                    for x in self.genitems(rep.result, keywordexpr):
                        yield x 
                self.config.hook.pytest_collectreport(report=rep)
            if self.shouldstop:
                break

    def filteritems(self, colitems):
        """ return items to process (some may be deselected)"""
        keywordexpr = self.config.option.keyword 
        if not keywordexpr or self._nomatch:
            return colitems
        if keywordexpr[-1] == ":": 
            keywordexpr = keywordexpr[:-1]
        remaining = []
        deselected = []
        for colitem in colitems:
            if isinstance(colitem, Item):
                if colitem._skipbykeyword(keywordexpr):
                    deselected.append(colitem)
                    continue
            remaining.append(colitem)
        if deselected: 
            self.config.hook.pytest_deselected(items=deselected)
            if self.config.option.keyword.endswith(":"):
                self._nomatch = True
        return remaining 

    def collect(self, colitems): 
        keyword = self.config.option.keyword
        for x in self.genitems(colitems, keyword):
            yield x

    def sessionstarts(self):
        """ setup any neccessary resources ahead of the test run. """
        self.config.hook.pytest_sessionstart(session=self)
        
    def pytest_runtest_logreport(self, report):
        if report.failed:
            self._testsfailed = True
            if self.config.option.exitfirst:
                self.shouldstop = True
    pytest_collectreport = pytest_runtest_logreport

    def sessionfinishes(self, exitstatus):
        """ teardown any resources after a test run. """ 
        self.config.hook.pytest_sessionfinish(
            session=self, 
            exitstatus=exitstatus, 
        )

    def main(self, colitems):
        """ main loop for running tests. """
        self.shouldstop = False 
        self.sessionstarts()
        exitstatus = EXIT_OK
        try:
            self._mainloop(colitems)
            if self._testsfailed:
                exitstatus = EXIT_TESTSFAILED
            self.sessionfinishes(exitstatus=exitstatus)
        except KeyboardInterrupt:
            excinfo = py.code.ExceptionInfo()
            self.config.hook.pytest_keyboard_interrupt(excinfo=excinfo)
            exitstatus = EXIT_INTERRUPTED
        except:
            excinfo = py.code.ExceptionInfo()
            self.config.pluginmanager.notify_exception(excinfo)
            exitstatus = EXIT_INTERNALERROR
        if exitstatus in (EXIT_INTERNALERROR, EXIT_INTERRUPTED):
            self.sessionfinishes(exitstatus=exitstatus)
        return exitstatus

    def _mainloop(self, colitems):
        for item in self.collect(colitems): 
            if self.shouldstop: 
                break 
            if not self.config.option.collectonly: 
                item.config.hook.pytest_runtest_protocol(item=item)
