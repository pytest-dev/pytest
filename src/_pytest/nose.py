"""Run testsuites written for nose."""
from _pytest import python
from _pytest import unittest
from _pytest.config import hookimpl
from _pytest.fixtures import getfixturemarker
from _pytest.nodes import Item


@hookimpl(trylast=True)
def pytest_runtest_setup(item) -> None:
    if is_potential_nosetest(item):
        if not call_optional(item.obj, "setup"):
            # Call module level setup if there is no object level one.
            call_optional(item.parent.obj, "setup")
        # XXX This implies we only call teardown when setup worked.
        item.addfinalizer(lambda: teardown_nose(item))


def teardown_nose(item) -> None:
    if is_potential_nosetest(item):
        if not call_optional(item.obj, "teardown"):
            call_optional(item.parent.obj, "teardown")


def is_potential_nosetest(item: Item) -> bool:
    # Extra check needed since we do not do nose style setup/teardown
    # on direct unittest style classes.
    return isinstance(item, python.Function) and not isinstance(
        item, unittest.TestCaseFunction
    )


def call_optional(obj: object, name: str) -> bool:
    method = getattr(obj, name, None)
    if method is None:
        return False
    is_fixture = getfixturemarker(method) is not None
    if is_fixture:
        return False
    if not callable(method):
        return False
    # If there are any problems allow the exception to raise rather than
    # silently ignoring it.
    method()
    return True
