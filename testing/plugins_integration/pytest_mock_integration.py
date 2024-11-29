# mypy: allow-untyped-defs
from __future__ import annotations


def test_mocker(mocker):
    mocker.MagicMock()
