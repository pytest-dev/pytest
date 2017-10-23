import pytest

from _pytest import fixtures


@pytest.mark.parametrize("baseid, nodeid, expected", (
    ('', '', True),
    ('', 'foo', True),
    ('', 'foo/bar', True),
    ('', 'foo/bar::TestBaz::()', True),
    ('foo', 'food', False),
    ('foo/bar::TestBaz::()', 'foo/bar', False),
    ('foo/bar::TestBaz::()', 'foo/bar::TestBop::()', False),
    ('foo/bar', 'foo/bar::TestBop::()', True),
))
def test_fixturemanager_ischildnode(baseid, nodeid, expected):
    result = fixtures.FixtureManager._ischildnode(baseid, nodeid)
    assert result is expected
