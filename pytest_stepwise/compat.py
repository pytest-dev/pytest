import pytest

try:
    from _pytest.cacheprovider import Cache
except ImportError:
    from pytest_cache import Cache

try:
    # pytest 3.7+
    Cache = Cache.for_config
except AttributeError:
    pass


if hasattr(pytest, 'hookimpl'):
    tryfirst = pytest.hookimpl(tryfirst=True)
else:
    tryfirst = pytest.mark.tryfirst
