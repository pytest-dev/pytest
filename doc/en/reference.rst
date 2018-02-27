
Reference
=========

This page contains the full reference to pytest's API.

.. contents::
    :depth: 2
    :local:


approx
------

.. autofunction:: _pytest.python_api.approx

outcomes
--------

You can use the following functions in your test, fixture or setup
functions to force a certain test outcome.  Note that most often
you can rather use declarative marks, see :ref:`skipping`.

pytest.fail
~~~~~~~~~~~

.. autofunction:: _pytest.outcomes.fail

pytest.skip
~~~~~~~~~~~

.. autofunction:: _pytest.outcomes.skip

pytest.importorskip
~~~~~~~~~~~~~~~~~~~

.. autofunction:: _pytest.outcomes.importorskip

pytest.xfail
~~~~~~~~~~~~

.. autofunction:: _pytest.outcomes.xfail

pytest.exit
~~~~~~~~~~~

.. autofunction:: _pytest.outcomes.exit

pytest.main
~~~~~~~~~~~

.. autofunction:: _pytest.config.main

pytest.raises
-------------

.. autofunction:: _pytest.python_api.raises
    :with: excinfo

Examples at :ref:`assertraises`.

pytest.deprecated_call
----------------------

.. autofunction:: _pytest.recwarn.deprecated_call
    :with:

.. _`hook-reference`:

Hooks
-----


.. currentmodule:: _pytest.hookspec

Reference to all hooks which can be implemented by :ref:`conftest.py files <localplugin>` and :ref:`plugins <plugins>`.

Bootstrapping hooks
~~~~~~~~~~~~~~~~~~~

Bootstrapping hooks called for plugins registered early enough (internal and setuptools plugins).

.. autofunction:: pytest_load_initial_conftests
.. autofunction:: pytest_cmdline_preparse
.. autofunction:: pytest_cmdline_parse
.. autofunction:: pytest_cmdline_main

Initialization hooks
~~~~~~~~~~~~~~~~~~~~

Initialization hooks called for plugins and ``conftest.py`` files.

.. autofunction:: pytest_addoption
.. autofunction:: pytest_configure
.. autofunction:: pytest_unconfigure

Test running hooks
~~~~~~~~~~~~~~~~~~

All runtest related hooks receive a :py:class:`pytest.Item <_pytest.main.Item>` object.

.. autofunction:: pytest_runtestloop
.. autofunction:: pytest_runtest_protocol
.. autofunction:: pytest_runtest_logstart
.. autofunction:: pytest_runtest_logfinish
.. autofunction:: pytest_runtest_setup
.. autofunction:: pytest_runtest_call
.. autofunction:: pytest_runtest_teardown
.. autofunction:: pytest_runtest_makereport

For deeper understanding you may look at the default implementation of
these hooks in :py:mod:`_pytest.runner` and maybe also
in :py:mod:`_pytest.pdb` which interacts with :py:mod:`_pytest.capture`
and its input/output capturing in order to immediately drop
into interactive debugging when a test failure occurs.

The :py:mod:`_pytest.terminal` reported specifically uses
the reporting hook to print information about a test run.

Collection hooks
~~~~~~~~~~~~~~~~

``pytest`` calls the following hooks for collecting files and directories:

.. autofunction:: pytest_collection
.. autofunction:: pytest_ignore_collect
.. autofunction:: pytest_collect_directory
.. autofunction:: pytest_collect_file

For influencing the collection of objects in Python modules
you can use the following hook:

.. autofunction:: pytest_pycollect_makeitem
.. autofunction:: pytest_generate_tests
.. autofunction:: pytest_make_parametrize_id

After collection is complete, you can modify the order of
items, delete or otherwise amend the test items:

.. autofunction:: pytest_collection_modifyitems

Reporting hooks
~~~~~~~~~~~~~~~

Session related reporting hooks:

.. autofunction:: pytest_collectstart
.. autofunction:: pytest_itemcollected
.. autofunction:: pytest_collectreport
.. autofunction:: pytest_deselected
.. autofunction:: pytest_report_header
.. autofunction:: pytest_report_collectionfinish
.. autofunction:: pytest_report_teststatus
.. autofunction:: pytest_terminal_summary
.. autofunction:: pytest_fixture_setup
.. autofunction:: pytest_fixture_post_finalizer

And here is the central hook for reporting about
test execution:

.. autofunction:: pytest_runtest_logreport

You can also use this hook to customize assertion representation for some
types:

.. autofunction:: pytest_assertrepr_compare


Debugging/Interaction hooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are few hooks which can be used for special
reporting or interaction with exceptions:

.. autofunction:: pytest_internalerror
.. autofunction:: pytest_keyboard_interrupt
.. autofunction:: pytest_exception_interact
.. autofunction:: pytest_enter_pdb


Objects
-------

Full reference to objects accessible from :ref:`fixtures <fixture>` or hooks

.. autoclass:: _pytest.config.Config()
    :members:

.. autoclass:: _pytest.config.Parser()
    :members:

.. autoclass:: _pytest.nodes.Node()
    :members:

.. autoclass:: _pytest.nodes.Collector()
    :members:
    :show-inheritance:

.. autoclass:: _pytest.nodes.FSCollector()
    :members:
    :show-inheritance:

.. autoclass:: _pytest.main.Session()
    :members:
    :show-inheritance:

.. autoclass:: _pytest.nodes.Item()
    :members:
    :show-inheritance:

.. autoclass:: _pytest.python.Module()
    :members:
    :show-inheritance:

.. autoclass:: _pytest.python.Class()
    :members:
    :show-inheritance:

.. autoclass:: _pytest.python.Function()
    :members:
    :show-inheritance:

.. autoclass:: _pytest.fixtures.FixtureDef()
    :members:
    :show-inheritance:

.. autoclass:: _pytest.runner.CallInfo()
    :members:

.. autoclass:: _pytest.runner.TestReport()
    :members:
    :inherited-members:

.. autoclass:: pluggy._Result
    :members:

.. autofunction:: _pytest.config.get_plugin_manager()

.. autoclass:: _pytest.config.PytestPluginManager()
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pluggy.PluginManager()
    :members:

.. currentmodule:: _pytest.pytester

.. autoclass:: Testdir()
    :members: runpytest,runpytest_subprocess,runpytest_inprocess,makeconftest,makepyfile

.. autoclass:: RunResult()
    :members:

.. autoclass:: LineMatcher()
    :members:

.. autoclass:: _pytest.capture.CaptureFixture()
    :members:


Fixtures
--------

Fixtures are requested by test functions or other fixtures by declaring them as argument names.


Example of a test requiring a fixture:

.. code-block:: python

    def test_output(capsys):
        print('hello')
        out, err = capsys.readouterr()
        assert out == 'hello\n'


Example of a fixture requiring another fixture:

.. code-block:: python

    @pytest.fixture
    def db_session(tmpdir):
        fn = tmpdir / 'db.file'
        return connect(str(fn))

For more details, consult the full :ref:`fixtures docs <fixture>`.


fixture decorator
~~~~~~~~~~~~~~~~~

.. currentmodule:: _pytest.fixtures
.. autofunction:: fixture
    :decorator:


.. _`cache-api`:

config.cache
~~~~~~~~~~~~

The ``config.cache`` object allows other plugins and fixtures
to store and retrieve values across test runs. To access it from fixtures
request ``pytestconfig`` into your fixture and get it with ``pytestconfig.cache``.

Under the hood, the cache plugin uses the simple
``dumps``/``loads`` API of the :py:mod:`json` stdlib module.

.. currentmodule:: _pytest.cacheprovider

.. automethod:: Cache.get
.. automethod:: Cache.set
.. automethod:: Cache.makedir


capsys
~~~~~~

.. currentmodule:: _pytest.capture

.. autofunction:: capsys()
    :no-auto-options:

    Returns an instance of :py:class:`CaptureFixture`.

    Example:

    .. code-block:: python

        def test_output(capsys):
            print("hello")
            captured = capsys.readouterr()
            assert captured.out == "hello\n"


capsysbinary
~~~~~~~~~~~~

.. autofunction:: capsysbinary()
    :no-auto-options:

    Returns an instance of :py:class:`CaptureFixture`.

    Example:

    .. code-block:: python

        def test_output(capsysbinary):
            print("hello")
            captured = capsysbinary.readouterr()
            assert captured.out == b"hello\n"


capfd
~~~~~~

.. autofunction:: capfd()
    :no-auto-options:

    Returns an instance of :py:class:`CaptureFixture`.

    Example:

    .. code-block:: python

        def test_system_echo(capfd):
            os.system('echo "hello"')
            captured = capsys.readouterr()
            assert captured.out == "hello\n"


capfdbinary
~~~~~~~~~~~~

.. autofunction:: capfdbinary()
    :no-auto-options:

    Returns an instance of :py:class:`CaptureFixture`.

    Example:

    .. code-block:: python

        def test_system_echo(capfdbinary):
            os.system('echo "hello"')
            captured = capfdbinary.readouterr()
            assert captured.out == b"hello\n"


doctest_namespace
~~~~~~~~~~~~~~~~~

.. autofunction:: _pytest.doctest.doctest_namespace()

    Usually this fixture is used in conjunction with another ``autouse`` fixture:

    .. code-block:: python

        @pytest.fixture(autouse=True)
        def add_np(doctest_namespace):
            doctest_namespace['np'] = numpy

    For more details: :ref:`doctest_namespace`.


request
~~~~~~~

The ``request`` fixture is a special fixture providing information of the requesting test function.

.. autoclass:: _pytest.fixtures.FixtureRequest()
    :members:


pytestconfig
~~~~~~~~~~~~

.. autofunction:: _pytest.fixtures.pytestconfig()
    

record_xml_property
~~~~~~~~~~~~~~~~~~~

.. autofunction:: _pytest.junitxml.record_xml_property()
