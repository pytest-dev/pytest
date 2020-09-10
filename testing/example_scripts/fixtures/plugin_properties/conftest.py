import warnings

import pytest


class FunPlugin:
    @property
    def shouldnt_warn(self):
        warnings.warn("i_shouldnt_happen")
        print("if no warning but thus, then all is bad")

    @pytest.fixture
    def fix(self):
        pass


def pytest_configure(config):
    warnings.simplefilter("always", DeprecationWarning)
    config.pluginmanager.register(FunPlugin(), "fun")
