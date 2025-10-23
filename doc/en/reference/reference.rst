:tocdepth: 3

.. contents:: Table of Contents
    :depth: 2
    :local:

API Reference
=============

This page contains the full reference to all pytest functions and
fixtures.

.. _`pytest.ini`:
.. _`pytest.ini file`:
.. _`pytest.ini options`:

Configuration Options
---------------------

Here is a list of builtin configuration options that may be written in a ``pytest.ini`` (or ``.pytest.ini``),
``pyproject.toml``, ``tox.ini``, or ``setup.cfg`` file, usually located at the root of your repository.

All options must be under a ``[pytest]`` section (``[tool.pytest.ini_options]`` for ``pyproject.toml``).

.. note::
    Options from multiple differently-named files will be merged based on precedence,
    with ``pytest.ini`` (or ``.pytest.ini``) taking highest priority,
    followed by ``tox.ini``, and then ``setup.cfg`` or ``pyproject.toml``.

Configuration file options:

.. code-block:: text

    [pytest] INI-options in the first pytest.ini|pyproject.toml|tox.ini|setup.cfg file found:

      markers (linelist):   Register new markers for test functions
      empty_parameter_set_mark (string):
                            Default marker for empty parametersets
      norecursedirs (args): Directory patterns to avoid for recursion
      testpaths (args):     Directories to search for tests when no files or directories are given on the command line
      filterwarnings (linelist):
                            Each line specifies a pattern for warnings.filterwarnings
      consider_namespace_packages (bool):
                            Consider namespace packages when resolving module names
      usefixtures (args):   List of fixtures that will be applied to all test functions; semantically the same as applying the @pytest.mark.usefixtures decorator to all test functions
      python_files (args):  Glob-style file patterns for Python test module discovery
      python_classes (args):
                            Prefixes or glob names for Python test class discovery
      python_functions (args):
                            Prefixes or glob names for Python test function and method discovery
      disable_test_id_escaping_and_forfeit_all_rights_to_community_support (bool):
                            Disable string escape non-ASCII characters, could cause unwanted side effects(use at your own risk)
      console_output_style (string):
                            Console output: "classic", or with additional progress information ("progress" (percentage) | "count" | "progress-even-when-capture-no").
      verbosity_test_cases (string):
                            Specify verbosity level for test case execution; overrides the general verbosity level
      xfail_strict (bool):  Default for the strict parameter of xfail markers when not given explicitly (default: False)
      tmp_path_retention_count (string):
                            How many sessions should we keep the `tmp_path` directories, according to `tmp_path_retention_policy`.
      tmp_path_retention_policy (string):
                            Controls which directories created by the `tmp_path` fixture are kept around, based on test outcome. (all/failed/none)
      enable_assertion_pass_hook (bool):
                            Enables the pytest_assertion_pass hook. Make sure to delete any previously generated pyc cache files.
      verbosity_assertions (string):
                            Specify a verbosity level for assertions, overriding the general verbosity level.
      junit_suite_name (string):
                            Test suite name for JUnit report
      junit_logging (string):
                            Write captured log messages to JUnit report: one of no|log|system-out|system-err|out-err|all
      junit_log_passing_tests (bool):
                            Capture log information for passing tests to JUnit report:
      junit_duration_report (string):
                            Duration time to report: one of total|call
      junit_family (string):
                            Emit XML for schema: one of legacy|xunit1|xunit2
      doctest_optionflags (args):
                            Option flags for doctests
      doctest_encoding (string):
                            Encoding used for doctest files
      cache_dir (string):   Cache directory path
      log_level (string):   Default value for --log-level
      log_format (string):  Default value for --log-format
      log_date_format (string):
                            Default value for --log-date-format
      log_cli (bool):       Enable log display during test run (also known as "live logging")
      log_cli_level (string):
                            Default value for --log-cli-level
      log_cli_format (string):
                            Default value for --log-cli-format
      log_cli_date_format (string):
                            Default value for --log-cli-date-format
      log_file (string):    Default value for --log-file
      log_file_mode (string):
                            Default value for --log-file-mode
      log_file_level (string):
                            Default value for --log-file-level
      log_file_format (string):
                            Default value for --log-file-format
      log_file_date_format (string):
                            Default value for --log-file-date-format
      log_auto_indent (string):
                            Default value for --log-auto-indent
      faulthandler_timeout (string):
                            Dump the traceback of all threads if a test takes
                            more than TIMEOUT seconds to finish
      faulthandler_exit_on_timeout (bool):
                            Exit the test process if a test takes more than
                            faulthandler_timeout seconds to finish
      addopts (args):       Extra command line options
      minversion (string):  Minimally required pytest version
      pythonpath (paths):   Add paths to sys.path
      required_plugins (args):
                            Plugins that must be present for pytest to run

    Environment variables:

      CI                       When set to a non-empty value, pytest knows it is running in a CI process and does not truncate summary info
      BUILD_NUMBER             Equivalent to CI
      PYTEST_ADDOPTS           Extra command line options
      PYTEST_PLUGINS           Comma-separated plugins to load during startup.
                               Note: Unlike the -p command-line option, PYTEST_PLUGINS is processed before command-line arguments,
                               making it suitable for always loading plugins. Use -p for one-time plugin loading or testing.
      PYTEST_DISABLE_PLUGIN_AUTOLOAD Set to disable plugin auto-loading
      PYTEST_DEBUG             Set to enable debug tracing of pytest's internals


    to see available markers type: pytest --markers
    to see available fixtures type: pytest --fixtures
    (shown according to specified file_or_dir or current dir if not specified; fixtures with leading '_' are only shown with the '-v' option
