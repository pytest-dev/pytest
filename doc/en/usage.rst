
.. _usage:

Usage and Invocations
==========================================


.. _cmdline:

Calling pytest through ``python -m pytest``
-----------------------------------------------------

.. versionadded:: 2.0

You can invoke testing through the Python interpreter from the command line::

    python -m pytest [...]

This is almost equivalent to invoking the command line script ``pytest [...]``
directly, except that Python will also add the current directory to ``sys.path``.

Possible exit codes
--------------------------------------------------------------

Running ``pytest`` can result in six different exit codes:

:Exit code 0: All tests were collected and passed successfully
:Exit code 1: Tests were collected and run but some of the tests failed
:Exit code 2: Test execution was interrupted by the user
:Exit code 3: Internal error happened while executing tests
:Exit code 4: pytest command line usage error
:Exit code 5: No tests were collected

Getting help on version, option names, environment variables
--------------------------------------------------------------

::

    pytest --version   # shows where pytest was imported from
    pytest --fixtures  # show available builtin function arguments
    pytest -h | --help # show help on command line and config file options


.. _maxfail:

Stopping after the first (or N) failures
---------------------------------------------------

To stop the testing process after the first (N) failures::

    pytest -x            # stop after first failure
    pytest --maxfail=2    # stop after two failures

.. _select-tests:

Specifying tests / selecting tests
---------------------------------------------------

Pytest supports several ways to run and select tests from the command-line.

**Run tests in a module**

::

    pytest test_mod.py

**Run tests in a directory**

::

    pytest testing/

**Run tests by keyword expressions**

::

    pytest -k "MyClass and not method"

This will run tests which contain names that match the given *string expression*, which can
include Python operators that use filenames, class names and function names as variables.
The example above will run ``TestMyClass.test_something``  but not ``TestMyClass.test_method_simple``.

.. _nodeids:

**Run tests by node ids**

Each collected test is assigned a unique ``nodeid`` which consist of the module filename followed
by specifiers like class names, function names and parameters from parametrization, separated by ``::`` characters.

To run a specific test within a module::

    pytest test_mod.py::test_func


Another example specifying a test method in the command line::

    pytest test_mod.py::TestClass::test_method

**Run tests by marker expressions**

::

    pytest -m slow

Will run all tests which are decorated with the ``@pytest.mark.slow`` decorator.

For more information see :ref:`marks <mark>`.

**Run tests from packages**

::

    pytest --pyargs pkg.testing
     
This will import ``pkg.testing`` and use its filesystem location to find and run tests from.
    

Modifying Python traceback printing
----------------------------------------------

Examples for modifying traceback printing::

    pytest --showlocals # show local variables in tracebacks
    pytest -l           # show local variables (shortcut)

    pytest --tb=auto    # (default) 'long' tracebacks for the first and last
                         # entry, but 'short' style for the other entries
    pytest --tb=long    # exhaustive, informative traceback formatting
    pytest --tb=short   # shorter traceback format
    pytest --tb=line    # only one line per failure
    pytest --tb=native  # Python standard library formatting
    pytest --tb=no      # no traceback at all

The ``--full-trace`` causes very long traces to be printed on error (longer
than ``--tb=long``). It also ensures that a stack trace is printed on
**KeyboardInterrupt** (Ctrl+C).
This is very useful if the tests are taking too long and you interrupt them
with Ctrl+C to find out where the tests are *hanging*. By default no output
will be shown (because KeyboardInterrupt is caught by pytest). By using this
option you make sure a trace is shown.


.. _pdb-option:

Dropping to PDB_ (Python Debugger) on failures
-----------------------------------------------

.. _PDB: http://docs.python.org/library/pdb.html

Python comes with a builtin Python debugger called PDB_.  ``pytest``
allows one to drop into the PDB_ prompt via a command line option::

    pytest --pdb

This will invoke the Python debugger on every failure.  Often you might
only want to do this for the first failing test to understand a certain
failure situation::

    pytest -x --pdb   # drop to PDB on first failure, then end test session
    pytest --pdb --maxfail=3  # drop to PDB for first three failures

Note that on any failure the exception information is stored on
``sys.last_value``, ``sys.last_type`` and ``sys.last_traceback``. In
interactive use, this allows one to drop into postmortem debugging with
any debug tool. One can also manually access the exception information,
for example::

    >>> import sys
    >>> sys.last_traceback.tb_lineno
    42
    >>> sys.last_value
    AssertionError('assert result == "ok"',)

.. _breakpoints:

Setting breakpoints
-------------------

.. versionadded: 2.4.0

To set a breakpoint in your code use the native Python ``import pdb;pdb.set_trace()`` call
in your code and pytest automatically disables its output capture for that test:

* Output capture in other tests is not affected.
* Any prior test output that has already been captured and will be processed as
  such.
* Any later output produced within the same test will not be captured and will
  instead get sent directly to ``sys.stdout``. Note that this holds true even
  for test output occurring after you exit the interactive PDB_ tracing session
  and continue with the regular test run.

.. _logging:

Logging
-------

.. versionadded 3.3.0

Log messages are captured by default and for each failed test will be shown in
the same manner as captured stdout and stderr.

Running without options::

    pytest

Shows failed tests like so::

    ----------------------- Captured stdlog call ----------------------
    test_reporting.py    26 INFO     text going to logger
    ----------------------- Captured stdout call ----------------------
    text going to stdout
    ----------------------- Captured stderr call ----------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

By default each captured log message shows the module, line number, log level
and message.  Showing the exact module and line number is useful for testing and
debugging.  If desired the log format and date format can be specified to
anything that the logging module supports.

Running pytest specifying formatting options::

    pytest --log-format="%(asctime)s %(levelname)s %(message)s" \
            --log-date-format="%Y-%m-%d %H:%M:%S"

Shows failed tests like so::

    ----------------------- Captured stdlog call ----------------------
    2010-04-10 14:48:44 INFO text going to logger
    ----------------------- Captured stdout call ----------------------
    text going to stdout
    ----------------------- Captured stderr call ----------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

These options can also be customized through a configuration file::

    [pytest]
    log_format = %(asctime)s %(levelname)s %(message)s
    log_date_format = %Y-%m-%d %H:%M:%S

Although the same effect could be achieved through the ``addopts`` setting,
using dedicated options should be preferred since the latter doesn't force other
developers to have ``pytest-catchlog`` installed (while at the same time,
``addopts`` approach would fail with 'unrecognized arguments' error). Command
line arguments take precedence.

Further it is possible to disable reporting logs on failed tests completely
with::

    pytest --no-print-logs

Or in you ``pytest.ini``::

  [pytest]
  log_print=False


Shows failed tests in the normal manner as no logs were captured::

    ----------------------- Captured stdout call ----------------------
    text going to stdout
    ----------------------- Captured stderr call ----------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

Inside tests it is possible to change the log level for the captured log
messages.  This is supported by the ``caplog`` fixture::

    def test_foo(caplog):
        caplog.set_level(logging.INFO)
        pass

By default the level is set on the handler used to catch the log messages,
however as a convenience it is also possible to set the log level of any
logger::

    def test_foo(caplog):
        caplog.set_level(logging.CRITICAL, logger='root.baz')
        pass

It is also possible to use a context manager to temporarily change the log
level::

    def test_bar(caplog):
        with caplog.at_level(logging.INFO):
            pass

Again, by default the level of the handler is affected but the level of any
logger can be changed instead with::

    def test_bar(caplog):
        with caplog.at_level(logging.CRITICAL, logger='root.baz'):
            pass

Lastly all the logs sent to the logger during the test run are made available on
the fixture in the form of both the LogRecord instances and the final log text.
This is useful for when you want to assert on the contents of a message::

    def test_baz(caplog):
        func_under_test()
        for record in caplog.records:
            assert record.levelname != 'CRITICAL'
        assert 'wally' not in caplog.text

For all the available attributes of the log records see the
``logging.LogRecord`` class.

You can also resort to ``record_tuples`` if all you want to do is to ensure,
that certain messages have been logged under a given logger name with a given
severity and message::

    def test_foo(caplog):
        logging.getLogger().info('boo %s', 'arg')

        assert caplog.record_tuples == [
            ('root', logging.INFO, 'boo arg'),
        ]

You can call ``caplog.clear()`` to reset the captured log records in a test::

    def test_something_with_clearing_records(caplog):
        some_method_that_creates_log_records()
        caplog.clear()
        your_test_method()
        assert ['Foo'] == [rec.message for rec in caplog.records]

Live Logs
^^^^^^^^^

By default, catchlog will output any logging records with a level higher or
equal to WARNING. In order to actually see these logs in the console you have to
disable pytest output capture by passing ``-s``.

You can specify the logging level for which log records with equal or higher
level are printed to the console by passing ``--log-cli-level``. This setting
accepts the logging level names as seen in python's documentation or an integer
as the logging level num.

Additionally, you can also specify ``--log-cli-format`` and
``--log-cli-date-format`` which mirror and default to ``--log-format`` and
``--log-date-format`` if not provided, but are applied only to the console
logging handler.

All of the CLI log options can also be set in the configuration INI file. The
option names are:

* ``log_cli_level``
* ``log_cli_format``
* ``log_cli_date_format``

If you need to record the whole test suite logging calls to a file, you can pass
``--log-file=/path/to/log/file``. This log file is opened in write mode which
means that it will be overwritten at each run tests session.

You can also specify the logging level for the log file by passing
``--log-file-level``. This setting accepts the logging level names as seen in
python's documentation(ie, uppercased level names) or an integer as the logging
level num.

Additionally, you can also specify ``--log-file-format`` and
``--log-file-date-format`` which are equal to ``--log-format`` and
``--log-date-format`` but are applied to the log file logging handler.

All of the log file options can also be set in the configuration INI file. The
option names are:

* ``log_file``
* ``log_file_level``
* ``log_file_format``
* ``log_file_date_format``


.. _durations:

Profiling test execution duration
-------------------------------------

.. versionadded: 2.2

To get a list of the slowest 10 test durations::

    pytest --durations=10


Creating JUnitXML format files
----------------------------------------------------

To create result files which can be read by Jenkins_ or other Continuous
integration servers, use this invocation::

    pytest --junitxml=path

to create an XML file at ``path``.

.. versionadded:: 3.1

To set the name of the root test suite xml item, you can configure the ``junit_suite_name`` option in your config file:

.. code-block:: ini

    [pytest]
    junit_suite_name = my_suite

record_xml_property
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 2.8

If you want to log additional information for a test, you can use the
``record_xml_property`` fixture:

.. code-block:: python

    def test_function(record_xml_property):
        record_xml_property("example_key", 1)
        assert 0

This will add an extra property ``example_key="1"`` to the generated
``testcase`` tag:

.. code-block:: xml

    <testcase classname="test_function" file="test_function.py" line="0" name="test_function" time="0.0009">
      <properties>
        <property name="example_key" value="1" />
      </properties>
    </testcase>

.. warning::

    ``record_xml_property`` is an experimental feature, and its interface might be replaced
    by something more powerful and general in future versions. The
    functionality per-se will be kept, however.

    Currently it does not work when used with the ``pytest-xdist`` plugin.

    Also please note that using this feature will break any schema verification.
    This might be a problem when used with some CI servers.

LogXML: add_global_property
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 3.0

If you want to add a properties node in the testsuite level, which may contains properties that are relevant
to all testcases you can use ``LogXML.add_global_properties``

.. code-block:: python

    import pytest

    @pytest.fixture(scope="session")
    def log_global_env_facts(f):

        if pytest.config.pluginmanager.hasplugin('junitxml'):
            my_junit = getattr(pytest.config, '_xml', None)

        my_junit.add_global_property('ARCH', 'PPC')
        my_junit.add_global_property('STORAGE_TYPE', 'CEPH')

    @pytest.mark.usefixtures(log_global_env_facts)
    def start_and_prepare_env():
        pass

    class TestMe(object):
        def test_foo(self):
            assert True

This will add a property node below the testsuite node to the generated xml:

.. code-block:: xml

    <testsuite errors="0" failures="0" name="pytest" skips="0" tests="1" time="0.006">
      <properties>
        <property name="ARCH" value="PPC"/>
        <property name="STORAGE_TYPE" value="CEPH"/>
      </properties>
      <testcase classname="test_me.TestMe" file="test_me.py" line="16" name="test_foo" time="0.000243663787842"/>
    </testsuite>

.. warning::

    This is an experimental feature, and its interface might be replaced
    by something more powerful and general in future versions. The
    functionality per-se will be kept.

Creating resultlog format files
----------------------------------------------------

.. deprecated:: 3.0

    This option is rarely used and is scheduled for removal in 4.0.

    An alternative for users which still need similar functionality is to use the
    `pytest-tap <https://pypi.python.org/pypi/pytest-tap>`_ plugin which provides
    a stream of test data.

    If you have any concerns, please don't hesitate to
    `open an issue <https://github.com/pytest-dev/pytest/issues>`_.

To create plain-text machine-readable result files you can issue::

    pytest --resultlog=path

and look at the content at the ``path`` location.  Such files are used e.g.
by the `PyPy-test`_ web page to show test results over several revisions.

.. _`PyPy-test`: http://buildbot.pypy.org/summary


Sending test report to online pastebin service
-----------------------------------------------------

**Creating a URL for each test failure**::

    pytest --pastebin=failed

This will submit test run information to a remote Paste service and
provide a URL for each failure.  You may select tests as usual or add
for example ``-x`` if you only want to send one particular failure.

**Creating a URL for a whole test session log**::

    pytest --pastebin=all

Currently only pasting to the http://bpaste.net service is implemented.

Disabling plugins
-----------------

To disable loading specific plugins at invocation time, use the ``-p`` option
together with the prefix ``no:``.

Example: to disable loading the plugin ``doctest``, which is responsible for
executing doctest tests from text files, invoke pytest like this::

    pytest -p no:doctest

.. _`pytest.main-usage`:

Calling pytest from Python code
----------------------------------------------------

.. versionadded:: 2.0

You can invoke ``pytest`` from Python code directly::

    pytest.main()

this acts as if you would call "pytest" from the command line.
It will not raise ``SystemExit`` but return the exitcode instead.
You can pass in options and arguments::

    pytest.main(['-x', 'mytestdir'])

You can specify additional plugins to ``pytest.main``::

    # content of myinvoke.py
    import pytest
    class MyPlugin(object):
        def pytest_sessionfinish(self):
            print("*** test run reporting finishing")

    pytest.main(["-qq"], plugins=[MyPlugin()])

Running it will show that ``MyPlugin`` was added and its
hook was invoked::

    $ python myinvoke.py
    *** test run reporting finishing
    

.. include:: links.inc
