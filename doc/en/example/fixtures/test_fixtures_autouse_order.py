import pytest

items = []


@pytest.fixture(autouse=True)
def autouse_function_fixture():
    items.append("auto_use_fixture")


@pytest.fixture()
def non_autouse_function_fixture():
    items.append("non_auto_use_fixture")


def test_fixture_autouse_ordering(
    non_autouse_function_fixture, autouse_function_fixture
):
    """
    You may (mistakenly) expect the test declaration order of fixtures to hold true here.
    However autouse=True fixtures are always given priority on a per scope basis.
    """
    assert items == ["non_auto_use_fixture", "auto_use_fixture"]  # failure
    assert items == ["auto_use_fixture", "non_auto_use_fixture"]  # pass
