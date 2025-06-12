from __future__ import annotations

from _pytest.fixtures import fixture


pytest_plugins = ["pytester", "some_plugin"]


@fixture
def b():
    return 1


@fixture
def a():
    return 2
