from __future__ import annotations

from typing import Generator

import pytest


# These tests will fail if run out of order, or selectively ... so they should probably be defined in a different way

executed: list[str] = []


#########
# Make sure setup and finalization is only run once when using fixture multiple times
# I'm pretty sure there's other tests that checks this already though, though idr fully where
#########
@pytest.fixture(scope="class")
def fixture_1() -> Generator[None, None, None]:
    executed.append("fix setup")
    yield
    executed.append("fix teardown")


class TestFixtureCaching:
    def test_1(self, fixture_1: None) -> None:
        assert executed == ["fix setup"]

    def test_2(self, fixture_1: None) -> None:
        assert executed == ["fix setup"]


def test_expected_setup_and_teardown() -> None:
    assert executed == ["fix setup", "fix teardown"]


######
# Make sure setup & finalization is only run once, with a cached exception
######
executed_crash: list[str] = []


@pytest.fixture(scope="class")
def fixture_crash(request: pytest.FixtureRequest) -> None:
    executed_crash.append("fix_crash setup")

    def my_finalizer() -> None:
        executed_crash.append("fix_crash teardown")

    request.addfinalizer(my_finalizer)

    raise Exception("foo")


class TestFixtureCachingException:
    @pytest.mark.xfail
    def test_crash_1(self, fixture_crash: None) -> None:
        assert False

    @pytest.mark.xfail
    def test_crash_2(self, fixture_crash: None) -> None:
        assert False


def test_crash_expected_setup_and_teardown() -> None:
    assert executed_crash == ["fix_crash setup", "fix_crash teardown"]
