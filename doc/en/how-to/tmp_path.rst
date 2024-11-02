
.. _`tmp_path handling`:
.. _tmp_path:

How to use temporary directories and files in tests
===================================================

The ``tmp_path`` fixture
------------------------

You can use the ``tmp_path`` fixture which will provide a temporary directory
unique to each test function.

``tmp_path`` is a :class:`pathlib.Path` object. Here is an example test usage:

.. code-block:: python

    # content of test_tmp_path.py
    CONTENT = "content"


    def test_create_file(tmp_path):
        d = tmp_path / "sub"
        d.mkdir()
        p = d / "hello.txt"
        p.write_text(CONTENT, encoding="utf-8")
        assert p.read_text(encoding="utf-8") == CONTENT
        assert len(list(tmp_path.iterdir())) == 1
        assert 0

Running this would result in a passed test except for the last
``assert 0`` line which we use to look at values:

.. code-block:: pytest

    $ pytest test_tmp_path.py
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-8.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project
    collected 1 item

    test_tmp_path.py F                                                   [100%]

    ================================= FAILURES =================================
    _____________________________ test_create_file _____________________________

    tmp_path = PosixPath('PYTEST_TMPDIR/test_create_file0')

        def test_create_file(tmp_path):
            d = tmp_path / "sub"
            d.mkdir()
            p = d / "hello.txt"
            p.write_text(CONTENT, encoding="utf-8")
            assert p.read_text(encoding="utf-8") == CONTENT
            assert len(list(tmp_path.iterdir())) == 1
    >       assert 0
    E       assert 0

    test_tmp_path.py:11: AssertionError
    ========================= short test summary info ==========================
    FAILED test_tmp_path.py::test_create_file - assert 0
    ============================ 1 failed in 0.12s =============================

By default, ``pytest`` retains the temporary directory for the last 3 ``pytest``
invocations. Concurrent invocations of the same test function are supported by
configuring the base temporary directory to be unique for each concurrent
run. See `temporary directory location and retention`_ for details.

.. _`tmp_path_factory example`:

The ``tmp_path_factory`` fixture
--------------------------------

The ``tmp_path_factory`` is a session-scoped fixture which can be used
to create arbitrary temporary directories from any other fixture or test.

For example, suppose your test suite needs a large image on disk, which is
generated procedurally. Instead of computing the same image for each test
that uses it into its own ``tmp_path``, you can generate it once per-session
to save time:

.. code-block:: python

    # contents of conftest.py
    import pytest


    @pytest.fixture(scope="session")
    def image_file(tmp_path_factory):
        img = compute_expensive_image()
        fn = tmp_path_factory.mktemp("data") / "img.png"
        img.save(fn)
        return fn


    # contents of test_image.py
    def test_histogram(image_file):
        img = load_image(image_file)
        # compute and test histogram

See :ref:`tmp_path_factory API <tmp_path_factory factory api>` for details.

.. _`tmpdir and tmpdir_factory`:
.. _tmpdir:

The ``tmpdir`` and ``tmpdir_factory`` fixtures
----------------------------------------------

The ``tmpdir`` and ``tmpdir_factory`` fixtures are similar to ``tmp_path``
and ``tmp_path_factory``, but use/return legacy `py.path.local`_ objects
rather than standard :class:`pathlib.Path` objects.

.. note::
    These days, it is preferred to use ``tmp_path`` and ``tmp_path_factory``.

    In order to help modernize old code bases, one can run pytest with the legacypath
    plugin disabled:

    .. code-block:: bash

        pytest -p no:legacypath

    This will trigger errors on tests using the legacy paths.
    It can also be permanently set as part of the :confval:`addopts` parameter in the
    config file.

See :fixture:`tmpdir <tmpdir>` :fixture:`tmpdir_factory <tmpdir_factory>`
API for details.


.. _`temporary directory location and retention`:

Temporary directory location and retention
------------------------------------------

The temporary directories,
as returned by the :fixture:`tmp_path` and (now deprecated) :fixture:`tmpdir` fixtures,
are automatically created under a base temporary directory,
in a structure that depends on the ``--basetemp`` option:

- By default (when the ``--basetemp`` option is not set),
  the temporary directories will follow this template:

  .. code-block:: text

      {temproot}/pytest-of-{user}/pytest-{num}/{testname}/

  where:

  - ``{temproot}`` is the system temporary directory
    as determined by :py:func:`tempfile.gettempdir`.
    It can be overridden by the :envvar:`PYTEST_DEBUG_TEMPROOT` environment variable.
  - ``{user}`` is the user name running the tests,
  - ``{num}`` is a number that is incremented with each test suite run
  - ``{testname}`` is a sanitized version of :py:attr:`the name of the current test <_pytest.nodes.Node.name>`.

  The auto-incrementing ``{num}`` placeholder provides a basic retention feature
  and avoids that existing results of previous test runs are blindly removed.
  By default, the last 3 temporary directories are kept,
  but this behavior can be configured with
  :confval:`tmp_path_retention_count` and :confval:`tmp_path_retention_policy`.

- When the ``--basetemp`` option is used (e.g. ``pytest --basetemp=mydir``),
  it will be used directly as base temporary directory:

  .. code-block:: text

      {basetemp}/{testname}/

  Note that there is no retention feature in this case:
  only the results of the most recent run will be kept.

  .. warning::

      The directory given to ``--basetemp`` will be cleared blindly before each test run,
      so make sure to use a directory for that purpose only.

When distributing tests on the local machine using ``pytest-xdist``, care is taken to
automatically configure a `basetemp` directory for the sub processes such that all temporary
data lands below a single per-test run temporary directory.

.. _`py.path.local`: https://py.readthedocs.io/en/latest/path.html
