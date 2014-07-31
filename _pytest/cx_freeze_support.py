"""
Package to support embedding pytest runner into executable files.

.. note:: Since we are imported into pytest namespace, we use local imports to
          be as cheap as possible.
"""

def includes():
    """
    Returns a list of module names used by py.test that should be
    included by cx_freeze.
    """
    import py
    import _pytest

    result = list(_iter_all_modules(py))
    result += list(_iter_all_modules(_pytest))

    # builtin files imported by pytest using py.std implicit mechanism;
    # should be removed if https://bitbucket.org/hpk42/pytest/pull-request/185
    # gets merged
    result += [
        'argparse',
        'shlex',
        'warnings',
        'types',
    ]
    return result


def _iter_all_modules(package, prefix=''):
    """
    Iterates over the names of all modules that can be found in the given
    package, recursively.

    Example:
        _iter_all_modules(_pytest) ->
            ['_pytest.assertion.newinterpret',
             '_pytest.capture',
             '_pytest.core',
             ...
            ]
    """
    import pkgutil
    import os

    if type(package) is not str:
        path, prefix = package.__path__[0], package.__name__ + '.'
    else:
        path = package
    for _, name, is_package in pkgutil.iter_modules([path]):
        if is_package:
            for m in _iter_all_modules(os.path.join(path, name), prefix=name + '.'):
                yield prefix + m
        else:
            yield prefix + name
