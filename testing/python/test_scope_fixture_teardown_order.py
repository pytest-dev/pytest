from typing import Generator

import pytest


last_executed = ""


@pytest.fixture(scope="module")
def fixture_1() -> Generator[None, None, None]:
    global last_executed
    assert last_executed == ""
    last_executed = "autouse_setup"
    yield
    assert last_executed == "noautouse_teardown"
    last_executed = "autouse_teardown"


@pytest.fixture(scope="module")
def fixture_2() -> Generator[None, None, None]:
    global last_executed
    assert last_executed == "autouse_setup"
    last_executed = "noautouse_setup"
    yield
    assert last_executed == "run_test"
    last_executed = "noautouse_teardown"


def test_autouse_fixture_teardown_order(fixture_1: None, fixture_2: None) -> None:
    global last_executed
    assert last_executed == "noautouse_setup"
    last_executed = "run_test"


def test_2(fixture_1: None) -> None:
    pass
