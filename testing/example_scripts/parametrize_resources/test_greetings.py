# mypy: allow-untyped-defs
from __future__ import annotations


def test_greeting(greeting):
    assert greeting in {"Hello", "Bonjour"}
