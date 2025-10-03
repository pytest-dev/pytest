# testing/test_match_markexpr.py
from __future__ import annotations

from _pytest.config.exceptions import UsageError
from _pytest.mark.expression import ParseError
import pytest


def test_public_api_present_match_markexpr() -> None:
    assert hasattr(pytest, "match_markexpr")
    assert callable(pytest.match_markexpr)


def test_strings_markexpr() -> None:
    assert pytest.match_markexpr("smoke or slow", "slow")
    assert not pytest.match_markexpr("smoke and slow", "smoke")


def test_iterables_markexpr() -> None:
    assert pytest.match_markexpr("smoke and not slow", ["smoke"])
    assert not pytest.match_markexpr("smoke and not slow", ["smoke", "slow"])
    assert pytest.match_markexpr("a and b", ["a", "b"])
    assert not pytest.match_markexpr("a and b", ["a"])


def test_invalid_expression_raises() -> None:
    with pytest.raises(
        ParseError, match="expected not OR left parenthesis OR identifier; got and"
    ):
        pytest.match_markexpr("smoke and and slow", ["smoke"])


def test_type_error_for_unsupported_target() -> None:
    with pytest.raises(
        UsageError,
        match="target must be an Item-like object, a marker name string, or an iterable of marker names",
    ):
        pytest.match_markexpr("smoke", 123)


def test_item_matching_with_request_node(request: pytest.FixtureRequest) -> None:
    request.config.addinivalue_line("markers", "smoke: test marker")
    request.config.addinivalue_line("markers", "slow: test marker")

    # Use the current test item; add/remove marks dynamically.
    request.node.add_marker("smoke")
    assert pytest.match_markexpr("smoke and not slow", request.node)
    assert not pytest.match_markexpr("slow", request.node)

    # Add another mark and re-check
    request.node.add_marker("slow")
    assert not pytest.match_markexpr("smoke and not slow", request.node)
    assert pytest.match_markexpr("smoke and slow", request.node)
