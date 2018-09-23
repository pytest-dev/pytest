import pytest


@pytest.mark.parameterize("a", [r"qwe/\abc"])
def test_fixture(tmpdir, a):
    tmpdir.check(dir=1)
    assert tmpdir.listdir() == []
