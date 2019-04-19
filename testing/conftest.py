import pytest


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Prefer faster tests.

    Use a hookwrapper to do this in the beginning, so e.g. --ff still works
    correctly.
    """
    fast_items = []
    slow_items = []
    neutral_items = []

    slow_fixturenames = ("testdir",)

    for item in items:
        try:
            fixtures = item.fixturenames
        except AttributeError:
            # doctest at least
            # (https://github.com/pytest-dev/pytest/issues/5070)
            neutral_items.append(item)
        else:
            if any(x for x in fixtures if x in slow_fixturenames):
                slow_items.append(item)
            else:
                marker = item.get_closest_marker("slow")
                if marker:
                    slow_items.append(item)
                else:
                    fast_items.append(item)

    items[:] = fast_items + neutral_items + slow_items

    yield
