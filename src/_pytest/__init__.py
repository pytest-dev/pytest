__all__ = ["__version__"]

try:
    from ._version import version

    __version__ = version  # type: str
except ImportError:
    # broken installation, we don't even try
    # unknown only works because we do poor mans version compare
    __version__ = "unknown"
