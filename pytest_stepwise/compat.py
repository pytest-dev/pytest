import pytest

try:
    from _pytest.cacheprovider import Cache
except ImportError:
    from pytest_cache import Cache


if hasattr(pytest, 'hookimpl'):
    tryfirst = pytest.hookimpl(tryfirst=True)
else:
    tryfirst = pytest.mark.tryfirst
