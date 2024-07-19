# mypy: allow-untyped-defs
from __future__ import annotations

import asyncio

import pytest


@pytest.mark.asyncio
async def test_sleep():
    await asyncio.sleep(0)
