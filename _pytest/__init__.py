__all__ = ['__version__']
import pkg_resources

try:
    __version__ = pkg_resources.get_distribution('pytest').version
except Exception:
    __version__ = None  # broken installation, we don't even try
