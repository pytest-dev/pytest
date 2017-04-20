import pkg_resources

__all__ = ['__version__']

try:
    __version__ = pkg_resources.get_distribution('pytest').version
except Exception:
    # broken installation, we don't even try
    # unknown only works because we do poor mans version compare
    __version__ = 'unknown'
