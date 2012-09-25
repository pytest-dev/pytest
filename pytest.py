"""
pytest: unit and functional testing with Python.
"""
__all__ = ['main']

if __name__ == '__main__': # if run as a script or by 'python -m pytest'
    # we trigger the below "else" condition by the following import
    import pytest
    raise SystemExit(pytest.main())
else:
    # we are simply imported
    from _pytest.core import main, UsageError, _preloadplugins
    from _pytest import core as cmdline
    from _pytest import __version__
    _preloadplugins() # to populate pytest.* namespace so help(pytest) works
