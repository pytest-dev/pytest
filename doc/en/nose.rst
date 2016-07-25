Running tests written for nose
=======================================

.. include:: links.inc

``pytest`` has basic support for running tests written for nose_.

.. _nosestyle:

Usage
-------------

After :ref:`installation` type::

    python setup.py develop  # make sure tests can import our package
    pytest  # instead of 'nosetests'

and you should be able to run your nose style tests and
make use of pytest's capabilities.

Supported nose Idioms
----------------------

* setup and teardown at module/class/method level
* SkipTest exceptions and markers
* setup/teardown decorators
* ``yield``-based tests and their setup
* ``__test__`` attribute on modules/classes/functions
* general usage of nose utilities

Unsupported idioms / known issues
----------------------------------

- unittest-style ``setUp, tearDown, setUpClass, tearDownClass``
  are recognized only on ``unittest.TestCase`` classes but not
  on plain classes.  ``nose`` supports these methods also on plain
  classes but pytest deliberately does not.  As nose and pytest already
  both support ``setup_class, teardown_class, setup_method, teardown_method``
  it doesn't seem useful to duplicate the unittest-API like nose does.
  If you however rather think pytest should support the unittest-spelling on
  plain classes please post `to this issue
  <https://github.com/pytest-dev/pytest/issues/377/>`_.

- nose imports test modules with the same import path (e.g.
  ``tests.test_mod``) but different file system paths
  (e.g. ``tests/test_mode.py`` and ``other/tests/test_mode.py``)
  by extending sys.path/import semantics.   pytest does not do that
  but there is discussion in `issue268 <https://github.com/pytest-dev/pytest/issues/268>`_ for adding some support.  Note that
  `nose2 choose to avoid this sys.path/import hackery <https://nose2.readthedocs.io/en/latest/differences.html#test-discovery-and-loading>`_.

- nose-style doctests are not collected and executed correctly,
  also doctest fixtures don't work.

- no nose-configuration is recognized.

- ``yield``-based methods don't support ``setup`` properly because
  the ``setup`` method is always called in the same class instance.
  There are no plans to fix this currently because ``yield``-tests
  are deprecated in pytest 3.0, with ``pytest.mark.parametrize``
  being the recommended alternative.


