try:
    from _pytest.cacheprovider import Cache
except ImportError:
    from pytest_cache import Cache
