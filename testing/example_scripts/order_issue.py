import os
import unittest

import pytest


class EnvironmentAwareMixin:
    @pytest.fixture(autouse=True)
    def _monkeypatch(self, monkeypatch):
        self._envpatcher = monkeypatch

    def set_environ(self, name, value):
        self._envpatcher.setenv(name, value)


# This arrangement fails: setup_method runs before _monkeypatch
class MyPytestBase(
    EnvironmentAwareMixin,
):
    pass


class TestSomething(MyPytestBase):
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.set_environ("X", "1")

    def test_something(self):
        assert os.environ["X"] == "1"


# This arrangement works: _monkeypatch runs before setUp
class MyUnittestBase(
    EnvironmentAwareMixin,
    unittest.TestCase,
):
    pass


class TestSomethingElse(MyUnittestBase):
    def setUp(self):
        self.set_environ("X", "1")

    def test_something_else(self):
        assert os.environ["X"] == "1"
