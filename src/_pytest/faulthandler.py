import io
import os
import sys
from typing import TextIO

import pytest
from _pytest.store import StoreKey


fault_handler_stderr_key = StoreKey[TextIO]()


def pytest_addoption(parser):
    help = (
        "Dump the traceback of all threads if a test takes "
        "more than TIMEOUT seconds to finish.\n"
        "Not available on Windows."
    )
    parser.addini("faulthandler_timeout", help, default=0.0)


def pytest_configure(config):
    import faulthandler

    if not faulthandler.is_enabled():
        # faulthhandler is not enabled, so install plugin that does the actual work
        # of enabling faulthandler before each test executes.
        config.pluginmanager.register(FaultHandlerHooks(), "faulthandler-hooks")
    else:
        from _pytest.warnings import _issue_warning_captured

        # Do not handle dumping to stderr if faulthandler is already enabled, so warn
        # users that the option is being ignored.
        timeout = FaultHandlerHooks.get_timeout_config_value(config)
        if timeout > 0:
            _issue_warning_captured(
                pytest.PytestConfigWarning(
                    "faulthandler module enabled before pytest configuration step, "
                    "'faulthandler_timeout' option ignored"
                ),
                config.hook,
                stacklevel=2,
            )


class FaultHandlerHooks:
    """Implements hooks that will actually install fault handler before tests execute,
    as well as correctly handle pdb and internal errors."""

    def pytest_configure(self, config):
        import faulthandler

        stderr_fd_copy = os.dup(self._get_stderr_fileno())
        config._store[fault_handler_stderr_key] = open(stderr_fd_copy, "w")
        faulthandler.enable(file=config._store[fault_handler_stderr_key])

    def pytest_unconfigure(self, config):
        import faulthandler

        faulthandler.disable()
        # close our dup file installed during pytest_configure
        # re-enable the faulthandler, attaching it to the default sys.stderr
        # so we can see crashes after pytest has finished, usually during
        # garbage collection during interpreter shutdown
        config._store[fault_handler_stderr_key].close()
        del config._store[fault_handler_stderr_key]
        faulthandler.enable(file=self._get_stderr_fileno())

    @staticmethod
    def _get_stderr_fileno():
        try:
            return sys.stderr.fileno()
        except (AttributeError, io.UnsupportedOperation):
            # pytest-xdist monkeypatches sys.stderr with an object that is not an actual file.
            # https://docs.python.org/3/library/faulthandler.html#issue-with-file-descriptors
            # This is potentially dangerous, but the best we can do.
            return sys.__stderr__.fileno()

    @staticmethod
    def get_timeout_config_value(config):
        return float(config.getini("faulthandler_timeout") or 0.0)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item):
        timeout = self.get_timeout_config_value(item.config)
        stderr = item.config._store[fault_handler_stderr_key]
        if timeout > 0 and stderr is not None:
            import faulthandler

            faulthandler.dump_traceback_later(timeout, file=stderr)
            try:
                yield
            finally:
                faulthandler.cancel_dump_traceback_later()
        else:
            yield

    @pytest.hookimpl(tryfirst=True)
    def pytest_enter_pdb(self):
        """Cancel any traceback dumping due to timeout before entering pdb.
        """
        import faulthandler

        faulthandler.cancel_dump_traceback_later()

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(self):
        """Cancel any traceback dumping due to an interactive exception being
        raised.
        """
        import faulthandler

        faulthandler.cancel_dump_traceback_later()
