.. _`cache_provider`:
.. _cache:


Cache: working with cross-testrun state
=======================================

.. versionadded:: 2.8

Usage
---------

The plugin provides two command line options to rerun failures from the
last ``pytest`` invocation:

* ``--lf``, ``--last-failed`` - to only re-run the failures.
* ``--ff``, ``--failed-first`` - to run the failures first and then the rest of
  the tests.

For cleanup (usually not needed), a ``--cache-clear`` option allows to remove
all cross-session cache contents ahead of a test run.

Other plugins may access the `config.cache`_ object to set/get
**json encodable** values between ``pytest`` invocations.

.. note::

    This plugin is enabled by default, but can be disabled if needed: see
    :ref:`cmdunregister` (the internal name for this plugin is
    ``cacheprovider``).


Rerunning only failures or failures first
-----------------------------------------------

First, let's create 50 test invocation of which only 2 fail::

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
    >          pytest.fail("bad luck")
    E          Failed: bad luck

    test_50.py:6: Failed
    _______________________________ test_num[25] _______________________________

    i = 25

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >          pytest.fail("bad luck")
    E          Failed: bad luck

    test_50.py:6: Failed
    2 failed, 48 passed in 0.12 seconds

If you then run it with ``--lf``:

.. code-block:: pytest

    $ pytest --lf
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-4.x.y, py-1.x.y, pluggy-0.x.y
    cachedir: $PYTHON_PREFIX/.pytest_cache
    rootdir: $REGENDOC_TMPDIR
    collected 50 items / 48 deselected / 2 selected
    run-last-failure: rerun previous 2 failures

    test_50.py FF                                                        [100%]

    ================================= FAILURES =================================
    _______________________________ test_num[17] _______________________________

    i = 17

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >          pytest.fail("bad luck")
    E          Failed: bad luck

    test_50.py:6: Failed
    _______________________________ test_num[25] _______________________________

    i = 25

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >          pytest.fail("bad luck")
    E          Failed: bad luck

    test_50.py:6: Failed
    ================= 2 failed, 48 deselected in 0.12 seconds ==================

You have run only the two failing test from the last run, while 48 tests have
not been run ("deselected").

Now, if you run with the ``--ff`` option, all tests will be run but the first
previous failures will be executed first (as can be seen from the series
of ``FF`` and dots):

.. code-block:: pytest

    $ pytest --ff
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-4.x.y, py-1.x.y, pluggy-0.x.y
    cachedir: $PYTHON_PREFIX/.pytest_cache
    rootdir: $REGENDOC_TMPDIR
    collected 50 items
    run-last-failure: rerun previous 2 failures first

    test_50.py FF................................................        [100%]

    ================================= FAILURES =================================
    _______________________________ test_num[17] _______________________________

    i = 17

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >          pytest.fail("bad luck")
    E          Failed: bad luck

    test_50.py:6: Failed
    _______________________________ test_num[25] _______________________________

    i = 25

        @pytest.mark.parametrize("i", range(50))
        def test_num(i):
            if i in (17, 25):
    >          pytest.fail("bad luck")
    E          Failed: bad luck

    test_50.py:6: Failed
    =================== 2 failed, 48 passed in 0.12 seconds ====================

.. _`config.cache`:

New ``--nf``, ``--new-first`` options: run new tests first followed by the rest
of the tests, in both cases tests are also sorted by the file modified time,
with more recent files coming first.

Behavior when no tests failed in the last run
---------------------------------------------

When no tests failed in the last run, or when no cached ``lastfailed`` data was
found, ``pytest`` can be configured either to run all of the tests or no tests,
using the ``--last-failed-no-failures`` option, which takes one of the following values:

.. code-block:: bash

    pytest --last-failed --last-failed-no-failures all    # run all tests (default behavior)
    pytest --last-failed --last-failed-no-failures none   # run no tests and exit

The new config.cache object
--------------------------------

.. regendoc:wipe

Plugins or conftest.py support code can get a cached value using the
pytest ``config`` object.  Here is a basic example plugin which
implements a :ref:`fixture` which re-uses previously created state
across pytest invocations::

    # content of test_caching.py
    import pytest
    import time

    def expensive_computation():
        print("running expensive computation...")

    @pytest.fixture
    def mydata(request):
        val = request.config.cache.get("example/value", None)
        if val is None:
            expensive_computation()
            val = 42
            request.config.cache.set("example/value", val)
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

    test_caching.py:17: AssertionError
    1 failed in 0.12 seconds

If you run it a second time the value will be retrieved from
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

    test_caching.py:17: AssertionError
    1 failed in 0.12 seconds

See the :ref:`cache-api` for more details.


Inspecting Cache content
-------------------------------

You can always peek at the content of the cache using the
``--cache-show`` command line option:

.. code-block:: pytest

    $ pytest --cache-show
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-4.x.y, py-1.x.y, pluggy-0.x.y
    cachedir: $PYTHON_PREFIX/.pytest_cache
    rootdir: $REGENDOC_TMPDIR
    cachedir: $PYTHON_PREFIX/.pytest_cache
    ------------------------------- cache values -------------------------------
    cache/lastfailed contains:
      {'a/test_db.py::test_a1': True,
       'a/test_db2.py::test_a2': True,
       'b/test_error.py::test_root': True,
       'failure_demo.py::TestCustomAssertMsg::test_custom_repr': True,
       'failure_demo.py::TestCustomAssertMsg::test_multiline': True,
       'failure_demo.py::TestCustomAssertMsg::test_single_line': True,
       'failure_demo.py::TestFailing::test_not': True,
       'failure_demo.py::TestFailing::test_simple': True,
       'failure_demo.py::TestFailing::test_simple_multiline': True,
       'failure_demo.py::TestMoreErrors::test_compare': True,
       'failure_demo.py::TestMoreErrors::test_complex_error': True,
       'failure_demo.py::TestMoreErrors::test_global_func': True,
       'failure_demo.py::TestMoreErrors::test_instance': True,
       'failure_demo.py::TestMoreErrors::test_startswith': True,
       'failure_demo.py::TestMoreErrors::test_startswith_nested': True,
       'failure_demo.py::TestMoreErrors::test_try_finally': True,
       'failure_demo.py::TestMoreErrors::test_z1_unpack_error': True,
       'failure_demo.py::TestMoreErrors::test_z2_type_error': True,
       'failure_demo.py::TestRaises::test_raise': True,
       'failure_demo.py::TestRaises::test_raises': True,
       'failure_demo.py::TestRaises::test_raises_doesnt': True,
       'failure_demo.py::TestRaises::test_reinterpret_fails_with_print_for_the_fun_of_it': True,
       'failure_demo.py::TestRaises::test_some_error': True,
       'failure_demo.py::TestRaises::test_tupleerror': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_attrs': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_dataclass': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_dict': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_list': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_list_long': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_long_text': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_long_text_multiline': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_longer_list': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_multiline_text': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_set': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_similar_text': True,
       'failure_demo.py::TestSpecialisedExplanations::test_eq_text': True,
       'failure_demo.py::TestSpecialisedExplanations::test_in_list': True,
       'failure_demo.py::TestSpecialisedExplanations::test_not_in_text_multiline': True,
       'failure_demo.py::TestSpecialisedExplanations::test_not_in_text_single': True,
       'failure_demo.py::TestSpecialisedExplanations::test_not_in_text_single_long': True,
       'failure_demo.py::TestSpecialisedExplanations::test_not_in_text_single_long_term': True,
       'failure_demo.py::test_attribute': True,
       'failure_demo.py::test_attribute_failure': True,
       'failure_demo.py::test_attribute_instance': True,
       'failure_demo.py::test_attribute_multiple': True,
       'failure_demo.py::test_dynamic_compile_shows_nicely': True,
       'failure_demo.py::test_generative[3-6]': True,
       'test_50.py::test_num[17]': True,
       'test_50.py::test_num[25]': True,
       'test_anothersmtp.py::test_showhelo': True,
       'test_assert1.py::test_function': True,
       'test_assert2.py::test_set_comparison': True,
       'test_backends.py::test_db_initialized[d2]': True,
       'test_caching.py::test_function': True,
       'test_checkconfig.py::test_something': True,
       'test_class.py::TestClass::test_two': True,
       'test_compute.py::test_compute[4]': True,
       'test_example.py::test_error': True,
       'test_example.py::test_fail': True,
       'test_foocompare.py::test_compare': True,
       'test_module.py::test_call_fails': True,
       'test_module.py::test_ehlo': True,
       'test_module.py::test_ehlo[mail.python.org]': True,
       'test_module.py::test_ehlo[smtp.gmail.com]': True,
       'test_module.py::test_event_simple': True,
       'test_module.py::test_fail1': True,
       'test_module.py::test_fail2': True,
       'test_module.py::test_func2': True,
       'test_module.py::test_interface_complex': True,
       'test_module.py::test_interface_simple': True,
       'test_module.py::test_noop': True,
       'test_module.py::test_noop[mail.python.org]': True,
       'test_module.py::test_noop[smtp.gmail.com]': True,
       'test_module.py::test_setup_fails': True,
       'test_parametrize.py::TestClass::test_equals[1-2]': True,
       'test_sample.py::test_answer': True,
       'test_show_warnings.py::test_one': True,
       'test_simple.yml::hello': True,
       'test_smtpsimple.py::test_ehlo': True,
       'test_step.py::TestUserHandling::test_modification': True,
       'test_strings.py::test_valid_string[!]': True,
       'test_tmp_path.py::test_create_file': True,
       'test_tmpdir.py::test_create_file': True,
       'test_tmpdir.py::test_needsfiles': True,
       'test_unittest_db.py::MyTest::test_method1': True,
       'test_unittest_db.py::MyTest::test_method2': True}
    cache/nodeids contains:
      ['test_caching.py::test_function']
    cache/stepwise contains:
      []
    example/value contains:
      42

    ======================= no tests ran in 0.12 seconds =======================

Clearing Cache content
-------------------------------

You can instruct pytest to clear all cache files and values
by adding the ``--cache-clear`` option like this:

.. code-block:: bash

    pytest --cache-clear

This is recommended for invocations from Continuous Integration
servers where isolation and correctness is more important
than speed.


Stepwise
--------

As an alternative to ``--lf -x``, especially for cases where you expect a large part of the test suite will fail, ``--sw``, ``--stepwise`` allows you to fix them one at a time. The test suite will run until the first failure and then stop. At the next invocation, tests will continue from the last failing test and then run until the next failing test. You may use the ``--stepwise-skip`` option to ignore one failing test and stop the test execution on the second failing test instead. This is useful if you get stuck on a failing test and just want to ignore it until later.
