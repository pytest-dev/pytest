.. image:: https://drone.io/bitbucket.org/pytest-dev/pytest/status.png
   :target: https://drone.io/bitbucket.org/pytest-dev/pytest/latest
.. image:: https://pypip.in/v/pytest/badge.png
   :target: https://pypi.python.org/pypi/pytest

Documentation: http://pytest.org/latest/

Changelog: http://pytest.org/latest/changelog.html

Issues: https://bitbucket.org/pytest-dev/pytest/issues?status=open

CI: https://drone.io/bitbucket.org/pytest-dev/pytest

The ``pytest`` testing tool makes it easy to write small tests, yet
scales to support complex functional testing.  It provides

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
  Python3.4, PyPy-2.3, (jython-2.5 untested)


- many `external plugins <http://pytest.org/latest/plugins.html#installing-external-plugins-searching>`_.

A simple example for a test::

    # content of test_module.py
    def test_function():
        i = 4
        assert i == 3

which can be run with ``py.test test_module.py``.  See `getting-started <http://pytest.org/latest/getting-started.html#our-first-test-run>`_ for more examples.

For much more info, including PDF docs, see

    http://pytest.org

and report bugs at:

    http://bitbucket.org/pytest-dev/pytest/issues/

and checkout or fork repo at:

    http://bitbucket.org/pytest-dev/pytest/


Copyright Holger Krekel and others, 2004-2014
Licensed under the MIT license.
