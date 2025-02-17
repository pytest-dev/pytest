import pytest

@pytest.fixture
def sample_fixture():
    return "Pytest Fixture"

def test_sample_fixture_behavior(sample_fixture):
    # Verify that the fixture is correctly returned
    assert sample_fixture == "Pytest Fixture"