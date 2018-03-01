
Reference
=========

This page contains the full reference to pytest's API.

.. contents::
    :depth: 3
    :local:

Functions
---------

pytest.approx
~~~~~~~~~~~~~

.. autofunction:: _pytest.python_api.approx

pytest.fail
~~~~~~~~~~~

**Tutorial**: :ref:`skipping`

.. autofunction:: _pytest.outcomes.fail

pytest.skip
~~~~~~~~~~~

.. autofunction:: _pytest.outcomes.skip(msg, [allow_module_level=False])

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

pytest.param
~~~~~~~~~~~~~

.. autofunction:: pytest.param(*values, [id], [marks])

pytest.raises
~~~~~~~~~~~~~

**Tutorial**: :ref:`assertraises`.

.. autofunction:: pytest.raises(expected_exception: Exception, [match], [message])
    :with: excinfo

pytest.deprecated_call
~~~~~~~~~~~~~~~~~~~~~~

**Tutorial**: :ref:`ensuring_function_triggers`.

.. autofunction:: pytest.deprecated_call()
    :with:

pytest.register_assert_rewrite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Tutorial**: :ref:`assertion-rewriting`.

.. autofunction:: pytest.register_assert_rewrite

pytest.warns
~~~~~~~~~~~~

**Tutorial**: :ref:`assertwarnings`

.. autofunction:: pytest.warns(expected_warning: Exception, [match])
    :with:


.. _`marks ref`:

Marks
-----

Marks can be used apply meta data to *test functions* (but not fixtures), which can then be accessed by
fixtures or plugins.


.. _`pytest.mark.parametrize ref`:

pytest.mark.parametrize
~~~~~~~~~~~~~~~~~~~~~~~

**Tutorial**: :doc:`parametrize`.

.. automethod:: _pytest.python.Metafunc.parametrize


.. _`pytest.mark.skip ref`:

pytest.mark.skip
~~~~~~~~~~~~~~~~

**Tutorial**: :ref:`skip`.

Unconditionally skip a test function.

.. py:function:: pytest.mark.skip(*, reason=None)

    :keyword str reason: Reason why the test function is being skipped.


.. _`pytest.mark.skipif ref`:

pytest.mark.skipif
~~~~~~~~~~~~~~~~~~

**Tutorial**: :ref:`xfail`.

Skip a test function if a condition is ``True``.

.. py:function:: pytest.mark.skipif(condition, *, reason=None)

    :type condition: bool or str
    :param condition: ``True/False`` if the condition should be skipped or a :ref:`condition string <string conditions>`.
    :keyword str reason: Reason why the test function is being skipped.


.. _`pytest.mark.xfail ref`:

pytest.mark.xfail
~~~~~~~~~~~~~~~~~~

**Tutorial**: :ref:`xfail`.

Marks a test function as *expected to fail*.

.. py:function:: pytest.mark.xfail(condition=None, *, reason=None, raises=None, run=True, strict=False)

    :type condition: bool or str
    :param condition: ``True/False`` if the condition should be marked as xfail or a :ref:`condition string <string conditions>`.
    :keyword str reason: Reason why the test function is marked as xfail.
    :keyword Exception raises: Exception subclass expected to be raised by the test function; other exceptions will fail the test.
    :keyword bool run:
        If the test function should actually be executed. If ``False``, the function will always xfail and will
        not be executed (useful a function is segfaulting).
    :keyword bool strict:
        * If ``False`` (the default) the function will be shown in the terminal output as ``xfailed`` if it fails
          and as ``xpass`` if it passes. In both cases this will not cause the test suite to fail as a whole. This
          is particularly useful to mark *flaky* tests (tests that random at fail) to be tackled later.
        * If ``True``, the function will be shown in the terminal output as ``xfailed`` if it fails, but if it
          unexpectedly passes then it will **fail** the test suite. This is particularly useful to mark functions
          that are always failing and there should be a clear indication if they unexpectedly start to pass (for example
          a new release of a library fixes a known bug).


custom marks
~~~~~~~~~~~~

Marks are created dynamically using the factory object ``pytest.mark`` and applied as a decorator.

For example:

.. code-block:: python

    @pytest.mark.timeout(10, 'slow', method='thread')
    def test_function():
        ...

Will create and attach a :class:`MarkInfo <_pytest.mark.MarkInfo>` object to the collected
:class:`Item <_pytest.nodes.Item>`, which can then be accessed by fixtures or hooks with
:meth:`Node.get_marker <_pytest.nodes.Node.get_marker>`. The ``mark`` object will have the following attributes:

.. code-block:: python

    mark.args == (10, 'slow')
    mark.kwargs == {'method': 'thread'}


Fixtures
--------

**Tutorial**: :ref:`fixture`.

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


@pytest.fixture
~~~~~~~~~~~~~~~

.. autofunction:: pytest.fixture
    :decorator:


.. _`cache-api`:

config.cache
~~~~~~~~~~~~

**Tutorial**: :ref:`cache`.

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

**Tutorial**: :doc:`capture`.

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

**Tutorial**: :doc:`capture`.

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

**Tutorial**: :doc:`capture`.

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

**Tutorial**: :doc:`capture`.

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

**Tutorial**: :doc:`doctest`.

.. autofunction:: _pytest.doctest.doctest_namespace()

    Usually this fixture is used in conjunction with another ``autouse`` fixture:

    .. code-block:: python

        @pytest.fixture(autouse=True)
        def add_np(doctest_namespace):
            doctest_namespace['np'] = numpy

    For more details: :ref:`doctest_namespace`.


request
~~~~~~~

**Tutorial**: :ref:`request example`.

The ``request`` fixture is a special fixture providing information of the requesting test function.

.. autoclass:: _pytest.fixtures.FixtureRequest()
    :members:


pytestconfig
~~~~~~~~~~~~

.. autofunction:: _pytest.fixtures.pytestconfig()


record_xml_property
~~~~~~~~~~~~~~~~~~~

**Tutorial**: :ref:`record_xml_property example`.

.. autofunction:: _pytest.junitxml.record_xml_property()

caplog
~~~~~~

**Tutorial**: :doc:`logging`.

.. autofunction:: _pytest.logging.caplog()
    :no-auto-options:

    This returns a :class:`_pytest.logging.LogCaptureFixture` instance.

.. autoclass:: _pytest.logging.LogCaptureFixture
    :members:


monkeypatch
~~~~~~~~~~~

.. currentmodule:: _pytest.monkeypatch

**Tutorial**: :doc:`monkeypatch`.

.. autofunction:: _pytest.monkeypatch.monkeypatch()
    :no-auto-options:

    This returns a :class:`MonkeyPatch` instance.

.. autoclass:: _pytest.monkeypatch.MonkeyPatch
    :members:

testdir
~~~~~~~

.. currentmodule:: _pytest.pytester

This fixture provides a :class:`Testdir` instance useful for black-box testing of test files, making it ideal to
test plugins.

To use it, include in your top-most ``conftest.py`` file::

    pytest_plugins = 'pytester'



.. autoclass:: Testdir()
    :members: runpytest,runpytest_subprocess,runpytest_inprocess,makeconftest,makepyfile

.. autoclass:: RunResult()
    :members:

.. autoclass:: LineMatcher()
    :members:


recwarn
~~~~~~~

**Tutorial**: :ref:`assertwarnings`

.. currentmodule:: _pytest.recwarn

.. autofunction:: recwarn()
    :no-auto-options:

.. autoclass:: _pytest.recwarn.WarningsRecorder()
    :members:

Each recorded warning is an instance of :class:`warnings.WarningMessage`.

.. note::
    :class:`RecordedWarning` was changed from a plain class to a namedtuple in pytest 3.1

.. note::
    ``DeprecationWarning`` and ``PendingDeprecationWarning`` are treated
    differently; see :ref:`ensuring_function_triggers`.


tmpdir
~~~~~~

**Tutorial**: :doc:`tmpdir`

.. currentmodule:: _pytest.tmpdir

.. autofunction:: tmpdir()
    :no-auto-options:


tmpdir_factory
~~~~~~~~~~~~~~

**Tutorial**: :ref:`tmpdir factory example`

.. _`tmpdir factory api`:

``tmpdir_factory`` instances have the following methods:

.. currentmodule:: _pytest.tmpdir

.. automethod:: TempdirFactory.mktemp
.. automethod:: TempdirFactory.getbasetemp


.. _`hook-reference`:

Hooks
-----

**Tutorial**: :doc:`writing_plugins`.

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
.. autofunction:: pytest_addhooks
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

Full reference to objects accessible from :ref:`fixtures <fixture>` or :ref:`hooks <hook-reference>`.


CallInfo
~~~~~~~~

.. autoclass:: _pytest.runner.CallInfo()
    :members:


Class
~~~~~

.. autoclass:: _pytest.python.Class()
    :members:
    :show-inheritance:

Collector
~~~~~~~~~

.. autoclass:: _pytest.nodes.Collector()
    :members:
    :show-inheritance:

Config
~~~~~~

.. autoclass:: _pytest.config.Config()
    :members:

ExceptionInfo
~~~~~~~~~~~~~

.. autoclass:: _pytest._code.ExceptionInfo
    :members:

FixtureDef
~~~~~~~~~~

.. autoclass:: _pytest.fixtures.FixtureDef()
    :members:
    :show-inheritance:

FSCollector
~~~~~~~~~~~

.. autoclass:: _pytest.nodes.FSCollector()
    :members:
    :show-inheritance:

Function
~~~~~~~~

.. autoclass:: _pytest.python.Function()
    :members:
    :show-inheritance:

Item
~~~~

.. autoclass:: _pytest.nodes.Item()
    :members:
    :show-inheritance:

MarkDecorator
~~~~~~~~~~~~~

.. autoclass:: _pytest.mark.MarkDecorator
    :members:

MarkGenerator
~~~~~~~~~~~~~

.. autoclass:: _pytest.mark.MarkGenerator
    :members:

MarkInfo
~~~~~~~~

.. autoclass:: _pytest.mark.MarkInfo
    :members:

Metafunc
~~~~~~~~

.. autoclass:: _pytest.python.Metafunc
    :members:

Module
~~~~~~

.. autoclass:: _pytest.python.Module()
    :members:
    :show-inheritance:

Node
~~~~

.. autoclass:: _pytest.nodes.Node()
    :members:

Parser
~~~~~~

.. autoclass:: _pytest.config.Parser()
    :members:

PluginManager
~~~~~~~~~~~~~

.. autoclass:: pluggy.PluginManager()
    :members:


PytestPluginManager
~~~~~~~~~~~~~~~~~~~

.. autoclass:: _pytest.config.PytestPluginManager()
    :members:
    :undoc-members:
    :show-inheritance:

Session
~~~~~~~

.. autoclass:: _pytest.main.Session()
    :members:
    :show-inheritance:

TestReport
~~~~~~~~~~

.. autoclass:: _pytest.runner.TestReport()
    :members:
    :inherited-members:

_Result
~~~~~~~

.. autoclass:: pluggy._Result
    :members:

Special Variables
-----------------

pytest treats some global variables in a special manner when defined in a test module.


pytest_plugins
~~~~~~~~~~~~~~

**Tutorial**: :ref:`available installable plugins`

Can be declared at the **global** level in *test modules* and *conftest.py files* to register additional plugins.
Can be either a ``str`` or ``Sequence[str]``.

.. code-block:: python

    pytest_plugins = "myapp.testsupport.myplugin"

.. code-block:: python

    pytest_plugins = ("myapp.testsupport.tools", "myapp.testsupport.regression")


pytest_mark
~~~~~~~~~~~

**Tutorial**: :ref:`scoped-marking`

Can be declared at the **global** level in *test modules* to apply one or more :ref:`marks <marks ref>` to all
test functions and methods. Can be either a single mark or a sequence of marks.

.. code-block:: python

    import pytest
    pytestmark = pytest.mark.webtest


.. code-block:: python

    import pytest
    pytestmark = (pytest.mark.integration, pytest.mark.slow)


