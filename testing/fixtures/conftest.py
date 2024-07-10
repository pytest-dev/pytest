import pytest

num_test = 0

@pytest.fixture
def fixture_test():
    """to be extended by same-name fixture in module"""
    global num_test
    num_test += 1
    print("->test [conftest]")
    return num_test


@pytest.fixture
def fixture_test_2(fixture_test):
    """should pick up extended fixture_test, even if it's not defined yet"""
    print("->test_2 [conftest]")
    return fixture_test


@pytest.fixture
def fixt_1():
    """part of complex dependency chain"""
    return "f1_c"


@pytest.fixture
def fixt_2(fixt_1):
    """part of complex dependency chain"""
    return f"f2_c({fixt_1})"


@pytest.fixture
def fixt_3(fixt_1):
    """part of complex dependency chain"""
    return f"f3_c({fixt_1})"
