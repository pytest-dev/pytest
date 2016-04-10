import io
import sys
import logging
import contextlib

import pytest


@contextlib.contextmanager
def captured_stderr():
    """Return a context manager used by stderr
    that temporarily replaces the sys stream stderr with a StringIO."""
    orig_stdout = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield sys.stderr
    finally:
        sys.stderr = orig_stdout


log_foo = logging.getLogger('foo')
log_foobar = logging.getLogger('foo.bar')
log_quux = logging.getLogger('quux')


class TestLogs:

    @contextlib.contextmanager
    def assertNoStderr(self):
        with captured_stderr() as buf:
            yield
        assert buf.getvalue() == ""

    def assertLogRecords(self, records, matches):
        assert len(records) == len(matches)
        for rec, match in zip(records, matches):
            assert isinstance(rec, logging.LogRecord)
            for k, v in match.items():
                assert getattr(rec, k) == v

    def test_logs_defaults(self):
        with self.assertNoStderr():
            with pytest.logs() as cm:
                log_foo.info("1")
                log_foobar.debug("2")
            assert cm.output == ["INFO:foo:1"]
            self.assertLogRecords(cm.records, [{'name': 'foo'}])

    def testAssertLogsTwoMatchingMessages(self):
        # Same, but with two matching log messages
        with self.assertNoStderr():
            with pytest.logs() as cm:
                log_foo.info("1")
                log_foobar.debug("2")
                log_quux.warning("3")
            assert cm.output == ["INFO:foo:1", "WARNING:quux:3"]
            self.assertLogRecords(cm.records,
                                  [{'name': 'foo'}, {'name': 'quux'}])

    def checkAssertLogsPerLevel(self, level):
        # Check level filtering
        with self.assertNoStderr():
            with pytest.logs(level=level) as cm:
                log_foo.warning("1")
                log_foobar.error("2")
                log_quux.critical("3")
            assert cm.output == ["ERROR:foo.bar:2", "CRITICAL:quux:3"]
            self.assertLogRecords(cm.records,
                                   [{'name': 'foo.bar'}, {'name': 'quux'}])

    def testAssertLogsPerLevel(self):
        self.checkAssertLogsPerLevel(logging.ERROR)
        self.checkAssertLogsPerLevel('ERROR')

    def checkAssertLogsPerLogger(self, logger):
        # Check per-logger fitering
        with self.assertNoStderr():
            with pytest.logs(level='DEBUG') as outer_cm:
                with pytest.logs(logger, level='DEBUG') as cm:
                    log_foo.info("1")
                    log_foobar.debug("2")
                    log_quux.warning("3")
                assert cm.output == ["INFO:foo:1", "DEBUG:foo.bar:2"]
                self.assertLogRecords(cm.records,
                                       [{'name': 'foo'}, {'name': 'foo.bar'}])
            # The outer catchall caught the quux log
            assert outer_cm.output == ["WARNING:quux:3"]

    def testAssertLogsPerLogger(self):
        self.checkAssertLogsPerLogger(logging.getLogger('foo'))
        self.checkAssertLogsPerLogger('foo')

    def testAssertLogsFailureNoLogs(self):
        # Failure due to no logs
        with self.assertNoStderr():
            with pytest.raises(pytest.fail.Exception):
                with pytest.logs():
                    pass

    def testAssertLogsFailureLevelTooHigh(self):
        # Failure due to level too high
        with self.assertNoStderr():
            with pytest.raises(pytest.fail.Exception):
                with pytest.logs(level='WARNING'):
                    log_foo.info("1")

    def testAssertLogsFailureMismatchingLogger(self):
        # Failure due to mismatching logger (and the logged message is
        # passed through)
        with pytest.logs('quux', level='ERROR'):
            with pytest.raises(pytest.fail.Exception):
                with pytest.logs('foo'):
                    log_quux.error("1")
