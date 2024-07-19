# mypy: allow-untyped-defs
from __future__ import annotations


def test_upper():
    assert "foo".upper() == "FOO"


def test_lower():
    assert "FOO".lower() == "foo"
