import pytest
from .compat import Cache


def pytest_addoption(parser):
    group = parser.getgroup('general')
    group.addoption('--sw', action='store_true', dest='stepwise',
                    help='alias for --stepwise')
    group.addoption('--stepwise', action='store_true', dest='stepwise',
                    help='exit on test fail and continue from last failing test next time')
    group.addoption('--skip', action='store_true', dest='skip',
                    help='ignore the first failing test but stop on the next failing test')


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    config.cache = Cache(config)
    config.pluginmanager.register(StepwisePlugin(config), 'stepwiseplugin')


class StepwisePlugin:
    def __init__(self, config):
        self.config = config
        self.active = config.getvalue('stepwise')
        self.session = None

        if self.active:
            self.lastfailed = config.cache.get('cache/stepwise', set())
            self.skip = config.getvalue('skip')

    def pytest_sessionstart(self, session):
        self.session = session

    def pytest_collection_modifyitems(self, session, config, items):
        if not self.active or not self.lastfailed:
            return

        already_passed = []
        found = False

        # Make a list of all tests that has been runned before the last failing one.
        for item in items:
            if item.nodeid in self.lastfailed:
                found = True
                break
            else:
                already_passed.append(item)

        # If the previously failed test was not found among the test items,
        # do not skip any tests.
        if not found:
            already_passed = []

        for item in already_passed:
            items.remove(item)

        config.hook.pytest_deselected(items=already_passed)

    def pytest_collectreport(self, report):
        if self.active and report.failed:
            self.session.shouldstop = 'Error when collecting test, stopping test execution.'

    def pytest_runtest_logreport(self, report):
        # Skip this hook if plugin is not active or the test is xfailed.
        if not self.active or 'xfail' in report.keywords:
            return

        if report.failed:
            if self.skip:
                # Remove test from the failed ones (if it exists) and unset the skip option
                # to make sure the following tests will not be skipped.
                self.lastfailed.discard(report.nodeid)
                self.skip = False
            else:
                # Mark test as the last failing and interrupt the test session.
                self.lastfailed.add(report.nodeid)
                self.session.shouldstop = 'Test failed, continuing from this test next run.'

        else:
            # If the test was actually run and did pass.
            if report.when == 'call':
                # Remove test from the failed ones, if exists.
                self.lastfailed.discard(report.nodeid)

    def pytest_sessionfinish(self, session):
        if self.active:
            self.config.cache.set('cache/stepwise', self.lastfailed)
        else:
            # Clear the list of failing tests if the plugin is not active.
            self.config.cache.set('cache/stepwise', set())
