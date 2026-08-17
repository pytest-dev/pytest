.. _`cache_provider`:
.. _cache:


How to re-run failed tests and maintain state between test runs
===============================================================



Usage
---------

The plugin provides two command line options to rerun failures from the
last ``pytest`` invocation:

* :option:`--lf, --last-failed <--lf>` - to only re-run the failures.
* :option:`--ff, --failed-first <--ff>` - to run the failures first and then the rest of
  the tests.

For cleanup (usually not needed), a :option:`--cache-clear` option allows to remove
all cross-session cache contents ahead of a test run.

Other plugins may access the `config.cache`_ object to set/get
**json encodable** values between ``pytest`` invocations.

.. note::

    This plugin is enabled by default, but can be disabled if needed: see
    :ref:`cmdunregister` (the internal name for this plugin is
    ``cacheprovider``).


Rerunning only failures or failures first
-----------------------------------------------

First, let's create 50 test invocations of which only 2 fail:

.. code-block:: python

    # content of test_50.py
    import pytest


    @pytest.mark.parametrize("i", range(50))
    def test_num(i):
        if i in (17, 25):
            pytest.fail("bad luck")

If you run this for the first time you will see two failures:

.. code-block:: pytest

    $ pytest -q
    .................F.......F........................                   [100%]
    ================================= FAILURES =================================
    _______________________________ test_num[17] _______________________________

    i = 17

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >           pytest.fail("bad luck")
    E           Failed: bad luck

    test_50.py:7: Failed
    _______________________________ test_num[25] _______________________________

    i = 25

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >           pytest.fail("bad luck")
    E           Failed: bad luck

    test_50.py:7: Failed
    ========================= short test summary info ==========================
    FAILED test_50.py::test_num[17] - Failed: bad luck
    FAILED test_50.py::test_num[25] - Failed: bad luck
    2 failed, 48 passed in 0.12s

If you then run it with :option:`--lf`:

.. code-block:: pytest

    $ pytest --lf
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project
    collected 2 items
    run-last-failure: rerun previous 2 failures

    test_50.py FF                                                        [100%]

    ================================= FAILURES =================================
    _______________________________ test_num[17] _______________________________

    i = 17

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >           pytest.fail("bad luck")
    E           Failed: bad luck

    test_50.py:7: Failed
    _______________________________ test_num[25] _______________________________

    i = 25

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >           pytest.fail("bad luck")
    E           Failed: bad luck

    test_50.py:7: Failed
    ========================= short test summary info ==========================
    FAILED test_50.py::test_num[17] - Failed: bad luck
    FAILED test_50.py::test_num[25] - Failed: bad luck
    ============================ 2 failed in 0.12s =============================

You have run only the two failing tests from the last run, while the 48 passing
tests have not been run ("deselected").

Now, if you run with the :option:`--ff` option, all tests will be run but the first
previous failures will be executed first (as can be seen from the series
of ``FF`` and dots):

.. code-block:: pytest

    $ pytest --ff
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project
    collected 50 items
    run-last-failure: rerun previous 2 failures first

    test_50.py FF................................................        [100%]

    ================================= FAILURES =================================
    _______________________________ test_num[17] _______________________________

    i = 17

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >           pytest.fail("bad luck")
    E           Failed: bad luck

    test_50.py:7: Failed
    _______________________________ test_num[25] _______________________________

    i = 25

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >           pytest.fail("bad luck")
    E           Failed: bad luck

    test_50.py:7: Failed
    ========================= short test summary info ==========================
    FAILED test_50.py::test_num[17] - Failed: bad luck
    FAILED test_50.py::test_num[25] - Failed: bad luck
    ======================= 2 failed, 48 passed in 0.12s =======================

.. _`config.cache`:

New :option:`--nf, --new-first <--nf>` option: run new tests first followed by the rest
of the tests, in both cases tests are also sorted by the file modified time,
with more recent files coming first.

Behavior when no tests failed in the last run
---------------------------------------------

The :option:`--lfnf, --last-failed-no-failures <--lfnf>` option governs the behavior of :option:`--last-failed`.
Determines whether to execute tests when there are no previously (known)
failures or when no cached ``lastfailed`` data was found.

There are two options:

* ``all``:  when there are no known test failures, runs all tests (the full test suite). This is the default.
* ``none``: when there are no known test failures, just emits a message stating this and exit successfully.

Example:

.. code-block:: bash

    pytest --last-failed --last-failed-no-failures all    # runs the full test suite (default behavior)
    pytest --last-failed --last-failed-no-failures none   # runs no tests and exits successfully

The new config.cache object
--------------------------------

.. regendoc:wipe

Plugins or conftest.py support code can get a cached value using the
pytest ``config`` object.  Here is a basic example plugin which
implements a :ref:`fixture <fixture>` which reuses previously created state
across pytest invocations:

.. code-block:: python

    # content of test_caching.py
    import pytest


    def expensive_computation():
        print("running expensive computation...")


    @pytest.fixture
    def mydata(pytestconfig):
        cache = getattr(pytestconfig, "cache", None)
        if cache is None:
            # pytestconfig not having the cache attribute means the
            # cache plugin is disabled.
            expensive_computation()
            return 42

        val = cache.get("example/value", None)
        if val is None:
            expensive_computation()
            val = 42
            cache.set("example/value", val)
        return val


    def test_function(mydata):
        assert mydata == 23

If you run this command for the first time, you can see the print statement:

.. code-block:: pytest

    $ pytest -q
    F                                                                    [100%]
    ================================= FAILURES =================================
    ______________________________ test_function _______________________________

    mydata = 42

        def test_function(mydata):
    >       assert mydata == 23
    E       assert 42 == 23

    test_caching.py:26: AssertionError
    -------------------------- Captured stdout setup ---------------------------
    running expensive computation...
    ========================= short test summary info ==========================
    FAILED test_caching.py::test_function - assert 42 == 23
    1 failed in 0.12s

If you run it a second time, the value will be retrieved from
the cache and nothing will be printed:

.. code-block:: pytest

    $ pytest -q
    F                                                                    [100%]
    ================================= FAILURES =================================
    ______________________________ test_function _______________________________

    mydata = 42

        def test_function(mydata):
    >       assert mydata == 23
    E       assert 42 == 23

    test_caching.py:26: AssertionError
    ========================= short test summary info ==========================
    FAILED test_caching.py::test_function - assert 42 == 23
    1 failed in 0.12s

See the :fixture:`config.cache fixture <cache>` for more details.


Inspecting Cache content
------------------------

You can always peek at the content of the cache using the
:option:`--cache-show` command line option:

.. code-block:: pytest

    $ pytest --cache-show
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project
    cachedir: /home/sweet/project/.pytest_cache
    --------------------------- cache values for '*' ---------------------------
    cache/lastfailed contains:
      {'test_caching.py::test_function': True}
    cache/nodeids contains:
      ['test_caching.py::test_function']
    example/value contains:
      42

    ========================== no tests ran in 0.12s ===========================

:option:`--cache-show` takes an optional argument to specify a glob pattern for
filtering:

.. code-block:: pytest

    $ pytest --cache-show example/*
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project
    cachedir: /home/sweet/project/.pytest_cache
    ----------------------- cache values for 'example/*' -----------------------
    example/value contains:
      42

    ========================== no tests ran in 0.12s ===========================

Clearing Cache content
----------------------

You can instruct pytest to clear all cache files and values
by adding the :option:`--cache-clear` option like this:

.. code-block:: bash

    pytest --cache-clear

This is recommended for invocations from Continuous Integration
servers where isolation and correctness is more important
than speed.


.. _cache_scopes:

Cache scopes
------------

.. versionadded:: 9.2

Not everything in the cache is equally portable. Which tests exist, and which are skipped, depends on the
interpreter running them, so the state behind :option:`--lf`, :option:`--nf` and :option:`--sw <--sw>` is
only meaningful for the environment that recorded it.

pytest keeps such values apart *within* a single cache directory, rather than needing one cache directory
per environment. Every cached value has a :class:`~pytest.CacheScope`:

.. list-table::
   :header-rows: 1

   * - Scope
     - Valid for
   * - :attr:`CacheScope.SHARED <pytest.CacheScope.SHARED>`
     - the project, whatever runs it. The default.
   * - :attr:`CacheScope.PYTHON <pytest.CacheScope.PYTHON>`
     - one Python implementation and ``major.minor`` version
   * - :attr:`CacheScope.ENV <pytest.CacheScope.ENV>`
     - one environment, i.e. one :data:`sys.prefix`

``--lf``, ``--nf`` and ``--sw`` use ``ENV``. Running a project under a tox or nox matrix, or simply under
two virtualenvs, therefore no longer has each run overwrite the previous one's last-failed set.

Plugins can do the same:

.. code-block:: python

    def pytest_configure(config):
        # Valid anywhere the project is.
        config.cache.set("myplugin/schema-version", 3)

        # Only valid for the environment that collected it.
        config.cache.set("myplugin/collected", ids, scope=pytest.CacheScope.ENV)

Reads must use the same scope they were written with. ``SHARED`` is the default, so existing plugins keep
working and keep their existing on-disk location.


.. _cache_location:

Where the cache is stored
-------------------------

.. versionadded:: 9.2

By default the cache lives in ``.pytest_cache`` inside the :ref:`rootdir <rootdir>`. The
:confval:`cache_policy` option chooses somewhere else by name:

.. code-block:: ini

    [pytest]
    cache_policy = user

``local``
    ``<rootdir>/.pytest_cache``. The default.

``user``
    A directory keyed by project inside the platform's user cache directory - ``$XDG_CACHE_HOME/pytest``
    or ``~/.cache/pytest`` on Linux, ``~/Library/Caches/pytest`` on macOS, ``%LOCALAPPDATA%\pytest\Cache``
    on Windows. Nothing at all is written into the project.

    This requires the ``xdg`` extra::

        pip install pytest[xdg]

:confval:`cache_dir` remains available and always wins: it is an explicit path, while ``cache_policy``
only chooses a location when ``cache_dir`` is unset. Use it for anywhere the two policies do not name -
it expands environment variables, so a cache inside the current virtualenv is:

.. code-block:: ini

    [pytest]
    cache_dir = $VIRTUAL_ENV/.pytest_cache

To opt in for a whole machine without editing every project, set the environment variable instead:

.. code-block:: bash

    export PYTEST_CACHE_POLICY=user

An explicit ``cache_policy`` in a config file still wins over it.

Under the ``user`` policy the directory is named after the project and a digest of its path, so it stays
recognisable::

    ~/.cache/pytest/myproject-1a2b3c4d5e6f7a8b/

The key is the rootdir alone - not the interpreter, which is handled by :ref:`cache scopes <cache_scopes>`
instead. One project therefore gets one cache directory however many environments run it. A *new*
directory only appears if the project itself moves.


.. _cache_pruning:

Listing and pruning caches
--------------------------

.. versionadded:: 9.2

A cache stored inside the project is deleted along with the project. One stored under the ``user`` policy
is not, so pytest can tell you what has accumulated:

.. code-block:: bash

    pytest --cache-list

.. code-block:: text

    user cache directory: /home/ronny/.cache/pytest

      DIRECTORY               SIZE      LAST USED  STATUS    ORIGIN
      myproject-1a2b3c4d5e6f  12.4 MiB  2 days     ok        /home/ronny/src/myproject
        env-venv-9f8e7d6c      1.1 MiB  2 days     ok        /home/ronny/src/myproject/.venv
        env-py312-0a1b2c3d   840.1 KiB  94 days    stale     /home/ronny/src/myproject/.tox/py312
      oldthing-9f8e7d6c5b4a  840.0 KiB  31 days    orphaned  /home/ronny/src/oldthing

    2 directories, 3 scopes, 13.2 MiB total

``orphaned`` means the origin project no longer exists, and ``stale`` means the environment a scope holds
state for no longer exists. In terminals which support it, the directory and origin columns are clickable
links.

Nothing is ever removed automatically. To remove things, say which:

.. code-block:: bash

    pytest --cache-prune=stale       # state for environments that are gone
    pytest --cache-prune=orphaned    # caches for projects that are gone
    pytest --cache-prune='oldthing-*'  # by name, or by origin path
    pytest --cache-prune=all

``--cache-prune`` requires a selector, so a bare invocation cannot delete anything, and it does not ask
for confirmation once given one - use ``--cache-list`` as the preview. ``all`` never removes the cache
directory of the project you run it from.

.. note::

    A project on an unmounted network or removable volume looks ``orphaned``, and a virtualenv on one
    looks ``stale``. This is the main reason pruning is never automatic.

.. note::

    ``--cache-list`` and ``--cache-prune`` only see the user-level cache root. Caches placed somewhere
    else with :confval:`cache_dir` are not tracked, since pytest has no way to know where they all are.


.. _cache stepwise:

Stepwise
--------

As an alternative to :option:`--lf` :option:`-x`, especially for cases where you expect a large part of the test suite will fail, :option:`--sw, --stepwise <--sw>` allows you to fix them one at a time. The test suite will run until the first failure and then stop. At the next invocation, tests will continue from the last failing test and then run until the next failing test. You may use the :option:`--stepwise-skip` option to ignore one failing test and stop the test execution on the second failing test instead. This is useful if you get stuck on a failing test and just want to ignore it until later.  Providing ``--stepwise-skip`` will also enable ``--stepwise`` implicitly.
