import pytest


class CustomItem(pytest.Item):
    def runtest(self):
        pass


def pytest_collect_file(path, parent):
    return CustomItem.from_parent(parent, fspath=path)
