.. _cli-options:

Command-line Options Reference
================================

Pytest provides numerous command-line options for controlling test discovery, execution,
reporting, configuration, and debugging. This reference covers the most commonly used
options, organized by functionality.

For a complete list of all available options, run:

.. code-block:: bash

    pytest --help

Or see the :ref:`complete command-line flag reference <command-line-flags>`.


Running and Selecting Tests
----------------------------

**Run tests by keyword expression**

The ``-k`` option lets you run tests matching a substring expression:

.. code-block:: bash

    pytest -k "expression"
    pytest -k "MyClass and not method"

This runs tests whose names match the given expression (case-insensitive). You can use
Python operators like ``and``, ``or``, and ``not``.

**Run tests by marker**

The ``-m`` option runs tests decorated with specific markers:

.. code-block:: bash

    pytest -m slow
    pytest -m "not slow"
    pytest -m "mark1 and not mark2"

See :ref:`marks <mark>` for more information on using markers.

**Exit on first failure**

.. code-block:: bash

    pytest -x               # Exit on first failure
    pytest --exitfirst      # Same as -x
    pytest --maxfail=2      # Exit after 2 failures

The ``-x`` / ``--exitfirst`` option stops the test run immediately on the first failure,
while ``--maxfail`` lets you specify how many failures to tolerate before stopping.

**Run previously failed tests**

.. code-block:: bash

    pytest --lf             # Run only last failed tests
    pytest --last-failed    # Same as --lf
    pytest --ff             # Run all tests, but failures first
    pytest --failed-first   # Same as --ff

These options use pytest's cache to rerun failed tests, useful for quickly iterating
on fixes. See :ref:`cache <cache>` for more information.

**Stepwise execution**

.. code-block:: bash

    pytest --sw             # Stop at first failure, continue from there next run
    pytest --stepwise       # Same as --sw

Stepwise mode stops at the first failure and continues from that test on the next run.


Output and Verbosity
--------------------

**Control verbosity**

.. code-block:: bash

    pytest -v               # Increase verbosity (show individual test names)
    pytest -vv              # Even more verbose
    pytest -q               # Decrease verbosity (quiet mode)
    pytest -qq              # Even quieter
    pytest --verbose        # Same as -v
    pytest --quiet          # Same as -q

The ``-v`` option shows more detail about test execution, while ``-q`` reduces output.

**Traceback formatting**

.. code-block:: bash

    pytest --tb=auto        # Default: intelligent traceback formatting
    pytest --tb=short       # Shorter traceback format
    pytest --tb=long        # Longer traceback format
    pytest --tb=line        # Only the failing line
    pytest --tb=native      # Python's standard traceback
    pytest --tb=no          # No traceback

The ``--tb`` option controls how tracebacks are displayed for failed tests.

**Show local variables**

.. code-block:: bash

    pytest -l               # Show local variables in tracebacks
    pytest --showlocals     # Same as -l

This adds local variable values to the traceback output, helpful for debugging.

**Summary information**

.. code-block:: bash

    pytest -r fE            # Show summary of failed and error tests (default)
    pytest -r a             # Show summary of all outcomes except passed
    pytest -r A             # Show summary of all outcomes
    pytest -r f             # Show only failed
    pytest -r fEsx          # Show failed, errors, skipped, xfailed

The ``-r`` option controls what appears in the test summary at the end of the run.

**Disable header and summary**

.. code-block:: bash

    pytest --no-header      # Don't show the header
    pytest --no-summary     # Don't show the summary


Reporting and Output Files
---------------------------

**JUnit XML reports**

.. code-block:: bash

    pytest --junit-xml=path/to/report.xml
    pytest --junit-prefix=myproject

Generate JUnit-style XML reports, useful for CI/CD integration.

**Duration reporting**

.. code-block:: bash

    pytest --durations=10           # Show 10 slowest tests
    pytest --durations=0            # Show all durations
    pytest --durations=5 --durations-min=1.0   # Show 5 slowest tests over 1 second

See :ref:`durations <durations>` for more details.

**Control output capture**

.. code-block:: bash

    pytest -s                       # Disable output capturing
    pytest --capture=no             # Same as -s
    pytest --capture=fd             # Capture at file descriptor level (default)
    pytest --capture=sys            # Capture at sys level

By default, pytest captures stdout/stderr. Use ``-s`` to see output in real-time.


Collection and Test Discovery
------------------------------

**Collect without running**

.. code-block:: bash

    pytest --collect-only   # Show which tests would be collected
    pytest --co             # Same as --collect-only

Useful for verifying test discovery without running tests.

**Import Python packages**

.. code-block:: bash

    pytest --pyargs pkg.testing

Import packages and run tests from their filesystem location.

**Ignore paths**

.. code-block:: bash

    pytest --ignore=path/to/ignore
    pytest --ignore-glob=**/old_*.py

Exclude specific paths or patterns from test collection.

**Configure conftest loading**

.. code-block:: bash

    pytest --confcutdir=dir     # Only load conftest.py relative to this directory
    pytest --noconftest         # Don't load any conftest.py files


Debugging
---------

**Python debugger**

.. code-block:: bash

    pytest --pdb            # Drop into debugger on failures
    pytest --trace          # Drop into debugger at the start of each test

**Show fixture setup**

.. code-block:: bash

    pytest --fixtures       # Show available fixtures
    pytest --setup-show     # Show fixture setup/teardown while running tests
    pytest --setup-only     # Only setup fixtures, don't run tests


Configuration
-------------

**Specify config file**

.. code-block:: bash

    pytest -c myconfig.ini          # Use specific config file
    pytest --config-file=pytest.ini

**Set base temporary directory**

.. code-block:: bash

    pytest --basetemp=dir   # Base directory for temporary files

**Override INI options**

.. code-block:: bash

    pytest -o xfail_strict=True -o cache_dir=.custom_cache
    pytest --override-ini=option=value


Logging
-------

**Set log levels**

.. code-block:: bash

    pytest --log-cli-level=INFO         # Set CLI logging level
    pytest --log-level=DEBUG            # Set capture log level
    pytest --log-file=tests.log         # Write logs to file

See :ref:`logging <logging>` for more information on pytest's logging capabilities.


Warnings
--------

**Control warning display**

.. code-block:: bash

    pytest --disable-warnings           # Disable warnings summary
    pytest -W ignore::DeprecationWarning  # Python warnings filter

See :ref:`warnings <warnings>` for more information.


Common Option Combinations
--------------------------

Here are some frequently used combinations:

.. code-block:: bash

    # Quick feedback loop - verbose, exit on first failure, show output
    pytest -vsx

    # Debugging failed test - show locals, drop to debugger, verbose
    pytest -lvx --pdb

    # CI/CD run - quiet, generate JUnit report, show durations
    pytest -q --junit-xml=report.xml --durations=10

    # Rerun failures with more detail
    pytest --lf -vv --tb=long

    # Show what would run without executing
    pytest --collect-only -q


See Also
--------

* :ref:`usage` - How to invoke pytest
* :ref:`Complete command-line flag reference <command-line-flags>` - Full list of all flags
* :ref:`Configuration <customize>` - Configure pytest via pytest.ini, pyproject.toml, etc.
* :ref:`Plugins <plugins>` - Extend pytest with plugins
