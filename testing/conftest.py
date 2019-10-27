import sys

import pytest

if sys.gettrace():

    @pytest.fixture(autouse=True)
    def restore_tracing():
        """Restore tracing function (when run with Coverage.py).

        https://bugs.python.org/issue37011
        """
        orig_trace = sys.gettrace()
        yield
        if sys.gettrace() != orig_trace:
            sys.settrace(orig_trace)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Prefer faster tests.

    Use a hookwrapper to do this in the beginning, so e.g. --ff still works
    correctly.
    """
    fast_items = []
    slow_items = []
    slowest_items = []
    neutral_items = []

    spawn_names = {"spawn_pytest", "spawn"}

    for item in items:
        try:
            fixtures = item.fixturenames
        except AttributeError:
            # doctest at least
            # (https://github.com/pytest-dev/pytest/issues/5070)
            neutral_items.append(item)
        else:
            if "testdir" in fixtures:
                co_names = item.function.__code__.co_names
                if spawn_names.intersection(co_names):
                    item.add_marker(pytest.mark.uses_pexpect)
                    slowest_items.append(item)
                elif "runpytest_subprocess" in co_names:
                    slowest_items.append(item)
                else:
                    slow_items.append(item)
                item.add_marker(pytest.mark.slow)
            else:
                marker = item.get_closest_marker("slow")
                if marker:
                    slowest_items.append(item)
                else:
                    fast_items.append(item)

    items[:] = fast_items + neutral_items + slow_items + slowest_items

    yield


@pytest.fixture
def tw_mock():
    """Returns a mock terminal writer"""

    class TWMock:
        WRITE = object()

        def __init__(self):
            self.lines = []
            self.is_writing = False

        def sep(self, sep, line=None):
            self.lines.append((sep, line))

        def write(self, msg, **kw):
            self.lines.append((TWMock.WRITE, msg))

        def line(self, line, **kw):
            self.lines.append(line)

        def markup(self, text, **kw):
            return text

        def get_write_msg(self, idx):
            flag, msg = self.lines[idx]
            assert flag == TWMock.WRITE
            return msg

        fullwidth = 80

    return TWMock()


@pytest.fixture
def dummy_yaml_custom_test(testdir):
    """Writes a conftest file that collects and executes a dummy yaml test.

    Taken from the docs, but stripped down to the bare minimum, useful for
    tests which needs custom items collected.
    """
    testdir.makeconftest(
        """
        import pytest

        def pytest_collect_file(parent, path):
            if path.ext == ".yaml" and path.basename.startswith("test"):
                return YamlFile(path, parent)

        class YamlFile(pytest.File):
            def collect(self):
                yield YamlItem(self.fspath.basename, self)

        class YamlItem(pytest.Item):
            def runtest(self):
                pass
    """
    )
    testdir.makefile(".yaml", test1="")
