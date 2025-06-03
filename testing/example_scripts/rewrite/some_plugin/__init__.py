import pytest

@pytest.fixture
def special_asserter():
    def special_assert(x, y):
        assert {'x': x} == {'x': y}
    return special_assert