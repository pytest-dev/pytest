:orphan:

.. _`pytest helpers`:

Pytest API and builtin fixtures
================================================


Most of the information of this page has been moved over to :ref:`api-reference`.

For information on plugin hooks and objects, see :ref:`plugins`.

For information on the ``pytest.mark`` mechanism, see :ref:`mark`.

For information about fixtures, see :ref:`fixtures`. To see a complete list of available fixtures (add ``-v`` to also see fixtures with leading ``_``), type :

.. code-block:: pytest

    $ pytest -q --fixtures
    cache -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/cacheprovider.py:519
        Return a cache object that can persist state between testing sessions.

    capsys -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/capture.py:903
        Enable text capturing of writes to ``sys.stdout`` and ``sys.stderr``.

    capsysbinary -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/capture.py:920
        Enable bytes capturing of writes to ``sys.stdout`` and ``sys.stderr``.

    capfd -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/capture.py:937
        Enable text capturing of writes to file descriptors ``1`` and ``2``.

    capfdbinary -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/capture.py:954
        Enable bytes capturing of writes to file descriptors ``1`` and ``2``.

    doctest_namespace [session scope] -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/doctest.py:722
        Fixture that returns a :py:class:`dict` that will be injected into the
        namespace of doctests.

    pytestconfig [session scope] -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/fixtures.py:1381
        Session-scoped fixture that returns the session's :class:`pytest.Config`
        object.

    record_property -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/junitxml.py:282
        Add extra properties to the calling test.

    record_xml_attribute -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/junitxml.py:305
        Add extra xml attributes to the tag for the calling test.

    record_testsuite_property [session scope] -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/junitxml.py:343
        Record a new ``<property>`` tag as child of the root ``<testsuite>``.

    caplog -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/logging.py:476
        Access and control log capturing.

    monkeypatch -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/monkeypatch.py:29
        A convenient fixture for monkey-patching.

    recwarn -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/recwarn.py:29
        Return a :class:`WarningsRecorder` instance that records all warnings emitted by test functions.

    tmpdir_factory [session scope] -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/tmpdir.py:210
        Return a :class:`pytest.TempdirFactory` instance for the test session.

    tmp_path_factory [session scope] -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/tmpdir.py:217
        Return a :class:`pytest.TempPathFactory` instance for the test session.

    tmpdir -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/tmpdir.py:232
        Return a temporary directory path object which is unique to each test
        function invocation, created as a sub directory of the base temporary
        directory.

    tmp_path -- ../../..$PYTHON_PREFIX/lib/python3.8/site-packages/_pytest/tmpdir.py:250
        Return a temporary directory path object which is unique to each test
        function invocation, created as a sub directory of the base temporary
        directory.


    no tests ran in 0.12s

You can also interactively ask for help, e.g. by typing on the Python interactive prompt something like:

.. code-block:: python

    import pytest

    help(pytest)
