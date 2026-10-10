"""Collect many generated methods sharing the same unittest class fixtures.

Run with ``pytest --collect-only bench/unittest_methods.py``.
"""

from __future__ import annotations

from unittest import TestCase


class TestManyMethods(TestCase):
    @classmethod
    def setUpClass(cls):
        pass


def test_method(self):
    pass


for i in range(35000):
    setattr(TestManyMethods, f"test_{i:05d}", test_method)

# Only collect the bound methods, not the helper function itself.
del test_method
