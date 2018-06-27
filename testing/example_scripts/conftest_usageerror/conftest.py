def pytest_configure(config):
    import pytest

    raise pytest.UsageError("hello")
