
.. _`non-python tests`:

Working with non-python tests
====================================================

.. _`yaml plugin`:

A basic example for specifying tests in Yaml files
--------------------------------------------------------------

.. _`pytest-yamlwsgi`: http://bitbucket.org/aafshar/pytest-yamlwsgi/src/tip/pytest_yamlwsgi.py
.. _`PyYAML`: http://pypi.python.org/pypi/PyYAML/

Here is an example ``conftest.py`` (extracted from Ali Afshnars special purpose `pytest-yamlwsgi`_ plugin).   This ``conftest.py`` will  collect ``test*.yml`` files and will execute the yaml-formatted content as custom tests:

.. include:: nonpython/conftest.py
    :literal:

You can create a simple example file:

.. include:: nonpython/test_simple.yml
    :literal:

and if you installed `PyYAML`_ or a compatible YAML-parser you can
now execute the test specification::

    nonpython $ pytest test_simple.yml
    ======= test session starts ========
    platform linux -- Python 3.x.y, pytest-3.x.y, py-1.x.y, pluggy-0.x.y
    rootdir: $REGENDOC_TMPDIR/nonpython, inifile:
    plugins: hypothesis-3.x.y
    collected 0 items / 1 errors
    
    ======= ERRORS ========
    _______ ERROR collecting test_simple.yml ________
    conftest.py:11: in collect
        import yaml # we need a yaml parser, e.g. PyYAML
    E   ImportError: No module named 'yaml'
    !!!!!!!!!!!!!!!!! Interrupted: 1 errors during collection !!!!!!!!!!!!!!!!!!
    ======= 1 error in 0.12 seconds ========

.. regendoc:wipe

You get one dot for the passing ``sub1: sub1`` check and one failure.
Obviously in the above ``conftest.py`` you'll want to implement a more
interesting interpretation of the yaml-values.  You can easily write
your own domain specific testing language this way.

.. note::

    ``repr_failure(excinfo)`` is called for representing test failures.
    If you create custom collection nodes you can return an error
    representation string of your choice.  It
    will be reported as a (red) string.

``reportinfo()`` is used for representing the test location and is also
consulted when reporting in ``verbose`` mode::

    nonpython $ pytest -v
    ======= test session starts ========
    platform linux -- Python 3.x.y, pytest-3.x.y, py-1.x.y, pluggy-0.x.y -- $PYTHON_PREFIX/bin/python3
    cachedir: .cache
    rootdir: $REGENDOC_TMPDIR/nonpython, inifile:
    plugins: hypothesis-3.x.y
    collecting ... collected 0 items / 1 errors
    
    ======= ERRORS ========
    _______ ERROR collecting test_simple.yml ________
    conftest.py:11: in collect
        import yaml # we need a yaml parser, e.g. PyYAML
    E   ImportError: No module named 'yaml'
    !!!!!!!!!!!!!!!!! Interrupted: 1 errors during collection !!!!!!!!!!!!!!!!!!
    ======= 1 error in 0.12 seconds ========

.. regendoc:wipe

While developing your custom test collection and execution it's also
interesting to just look at the collection tree::

    nonpython $ pytest --collect-only
    ======= test session starts ========
    platform linux -- Python 3.x.y, pytest-3.x.y, py-1.x.y, pluggy-0.x.y
    rootdir: $REGENDOC_TMPDIR/nonpython, inifile:
    plugins: hypothesis-3.x.y
    collected 0 items / 1 errors
    
    ======= ERRORS ========
    _______ ERROR collecting test_simple.yml ________
    conftest.py:11: in collect
        import yaml # we need a yaml parser, e.g. PyYAML
    E   ImportError: No module named 'yaml'
    !!!!!!!!!!!!!!!!! Interrupted: 1 errors during collection !!!!!!!!!!!!!!!!!!
    ======= 1 error in 0.12 seconds ========
