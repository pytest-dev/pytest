# mypy: allow-untyped-defs
from __future__ import annotations

import anyio

import pytest


@pytest.mark.anyio
async def test_sleep():
    await anyio.sleep(0)
