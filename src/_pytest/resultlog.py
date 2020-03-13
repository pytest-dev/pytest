""" log machine-parseable test session result information in a plain
text file.
"""
import os

import py

from _pytest.store import StoreKey


resultlog_key = StoreKey["ResultLog"]()


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "resultlog plugin options")
    group.addoption(
        "--resultlog",
        "--result-log",
        action="store",
        metavar="path",
        default=None,
        help="DEPRECATED path for machine-readable result log.",
    )


def pytest_configure(config):
    resultlog = config.option.resultlog
    # prevent opening resultlog on slave nodes (xdist)
    if resultlog and not hasattr(config, "slaveinput"):
        dirname = os.path.dirname(os.path.abspath(resultlog))
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        logfile = open(resultlog, "w", 1)  # line buffered
        config._store[resultlog_key] = ResultLog(config, logfile)
        config.pluginmanager.register(config._store[resultlog_key])

        from _pytest.deprecated import RESULT_LOG
        from _pytest.warnings import _issue_warning_captured

        _issue_warning_captured(RESULT_LOG, config.hook, stacklevel=2)


def pytest_unconfigure(config):
    resultlog = config._store.get(resultlog_key, None)
    if resultlog:
        resultlog.logfile.close()
        del config._store[resultlog_key]
        config.pluginmanager.unregister(resultlog)


class ResultLog:
    def __init__(self, config, logfile):
        self.config = config
        self.logfile = logfile  # preferably line buffered

    def write_log_entry(self, testpath, lettercode, longrepr):
        print("{} {}".format(lettercode, testpath), file=self.logfile)
        for line in longrepr.splitlines():
            print(" %s" % line, file=self.logfile)

    def log_outcome(self, report, lettercode, longrepr):
        testpath = getattr(report, "nodeid", None)
        if testpath is None:
            testpath = report.fspath
        self.write_log_entry(testpath, lettercode, longrepr)

    def pytest_runtest_logreport(self, report):
        if report.when != "call" and report.passed:
            return
        res = self.config.hook.pytest_report_teststatus(
            report=report, config=self.config
        )
        code = res[1]
        if code == "x":
            longrepr = str(report.longrepr)
        elif code == "X":
            longrepr = ""
        elif report.passed:
            longrepr = ""
        elif report.skipped:
            longrepr = str(report.longrepr[2])
        else:
            longrepr = str(report.longrepr)
        self.log_outcome(report, code, longrepr)

    def pytest_collectreport(self, report):
        if not report.passed:
            if report.failed:
                code = "F"
                longrepr = str(report.longrepr)
            else:
                assert report.skipped
                code = "S"
                longrepr = "%s:%d: %s" % report.longrepr
            self.log_outcome(report, code, longrepr)

    def pytest_internalerror(self, excrepr):
        reprcrash = getattr(excrepr, "reprcrash", None)
        path = getattr(reprcrash, "path", None)
        if path is None:
            path = "cwd:%s" % py.path.local()
        self.write_log_entry(path, "!", str(excrepr))
