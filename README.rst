======
pytest
======

The ``pytest`` testing tool makes it easy to write small tests, yet
scales to support complex functional testing.

.. image:: http://img.shields.io/pypi/v/pytest.svg
   :target: https://pypi.python.org/pypi/pytest
.. image:: http://img.shields.io/coveralls/pytest-dev/pytest/master.svg
   :target: https://coveralls.io/r/pytest-dev/pytest
.. image:: https://travis-ci.org/pytest-dev/pytest.svg?branch=master
    :target: https://travis-ci.org/pytest-dev/pytest
.. image:: https://ci.appveyor.com/api/projects/status/mrgbjaua7t33pg6b?svg=true
    :target: https://ci.appveyor.com/project/pytestbot/pytest

Documentation: http://pytest.org/latest/

Changelog: http://pytest.org/latest/changelog.html

Issues: https://github.com/pytest-dev/pytest/issues

Features
--------

- `auto-discovery
  <http://pytest.org/latest/goodpractises.html#python-test-discovery>`_
  of test modules and functions,
- detailed info on failing `assert statements <http://pytest.org/latest/assert.html>`_ (no need to remember ``self.assert*`` names)
- `modular fixtures <http://pytest.org/latest/fixture.html>`_  for
  managing small or parametrized long-lived test resources.
- multi-paradigm support: you can use ``pytest`` to run test suites based
  on `unittest <http://pytest.org/latest/unittest.html>`_ (or trial),
  `nose <http://pytest.org/latest/nose.html>`_
- single-source compatibility from Python2.6 all the way up to
  Python3.5, PyPy-2.3, (jython-2.5 untested)


- many `external plugins <http://pytest.org/latest/plugins.html#installing-external-plugins-searching>`_.

A simple example for a test:

.. code-block:: python

    # content of test_module.py
    def test_function():
        i = 4
        assert i == 3

which can be run with ``py.test test_module.py``.  See `getting-started <http://pytest.org/latest/getting-started.html#our-first-test-run>`_ for more examples.

For much more info, including PDF docs, see

    http://pytest.org

and report bugs at:

    https://github.com/pytest-dev/pytest/issues

and checkout or fork repo at:

    https://github.com/pytest-dev/pytest


Copyright Holger Krekel and others, 2004-2015
Licensed under the MIT license.
