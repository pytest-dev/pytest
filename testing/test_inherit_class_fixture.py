from __future__ import annotations

import typing

import pytest


class ParentBase:
    """from issue #14011"""

    name = ""
    variable = ""

    def setup(self) -> None:
        self.variable = self.name

    def teardown(self) -> None:
        pass

    @pytest.fixture(scope="class")
    def fix(self) -> typing.Generator[None]:
        self.setup()
        yield
        self.teardown()

    @pytest.fixture(scope="class", autouse=True)
    def base_autouse(self) -> None:
        self.flag = True


@pytest.mark.usefixtures("fix")
class Test1(ParentBase):
    name = "test1"

    def test_a(self) -> None:
        assert self.variable == self.name


@pytest.mark.usefixtures("fix")
class Test2(ParentBase):
    name = "test2"

    def test_a(self) -> None:
        assert self.variable == self.name


class TestChild(ParentBase):
    def test_flag(self) -> None:
        assert self.flag


class BaseTestClass:
    """from issue #10819"""

    test_func_scope_set = None
    test_class_scope_set = None

    @pytest.fixture(scope="class", autouse=True)
    def dummy_class_fixture(self) -> None:
        self.test_class_scope_set = True

    @pytest.fixture(scope="function", autouse=True)
    def dummy_func_fixture(self) -> None:
        self.test_func_scope_set = True


class TestDummy(BaseTestClass):
    def test_dummy(self) -> None:
        assert self.test_func_scope_set is True
        assert self.test_class_scope_set is True
