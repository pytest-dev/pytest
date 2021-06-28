.. _`cache_provider`:
.. _cache:


How to re-run failed tests and maintain state between test runs
===============================================================



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

First, let's create 50 test invocation of which only 2 fail:

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

If you then run it with ``--lf``:

.. code-block:: pytest

    $ pytest --lf
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-7.x.y, py-1.x.y, pluggy-0.x.y
    cachedir: $PYTHON_PREFIX/.pytest_cache
    rootdir: $REGENDOC_TMPDIR
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

Now, if you run with the ``--ff`` option, all tests will be run but the first
previous failures will be executed first (as can be seen from the series
of ``FF`` and dots):

.. code-block:: pytest

    $ pytest --ff
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-7.x.y, py-1.x.y, pluggy-0.x.y
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
implements a :ref:`fixture <fixture>` which re-uses previously created state
across pytest invocations:

.. code-block:: python

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

    test_caching.py:20: AssertionError
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

    test_caching.py:20: AssertionError
    ========================= short test summary info ==========================
    FAILED test_caching.py::test_function - assert 42 == 23
    1 failed in 0.12s

See the :fixture:`config.cache fixture <cache>` for more details.


Inspecting Cache content
------------------------

You can always peek at the content of the cache using the
``--cache-show`` command line option:

.. code-block:: pytest

    $ pytest --cache-show
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-7.x.y, py-1.x.y, pluggy-0.x.y
    cachedir: $PYTHON_PREFIX/.pytest_cache
    rootdir: $REGENDOC_TMPDIR
    cachedir: $PYTHON_PREFIX/.pytest_cache
    --------------------------- cache values for '*' ---------------------------
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
       'test_assert1.py::test_function': True,
       'test_assert2.py::test_set_comparison': True,
       'test_backends.py::test_db_initialized[d2]': True,
       'test_caching.py::test_function': True,
       'test_checkconfig.py::test_something': True,
       'test_class.py::TestClass::test_two': True,
       'test_class_demo.py::TestClassDemoInstance::test_two': True,
       'test_compute.py::test_compute[4]': True,
       'test_foocompare.py::test_compare': True,
       'test_module.py::test_call_fails': True,
       'test_module.py::test_event_simple': True,
       'test_module.py::test_fail1': True,
       'test_module.py::test_fail2': True,
       'test_module.py::test_interface_complex': True,
       'test_module.py::test_interface_simple': True,
       'test_module.py::test_setup_fails': True,
       'test_parametrize.py::TestClass::test_equals[1-2]': True,
       'test_sample.py::test_answer': True,
       'test_simple.yaml::hello': True,
       'test_step.py::TestUserHandling::test_modification': True,
       'test_tmp_path.py::test_needsfiles': True}
    cache/nodeids contains:
      ['a/test_db.py::test_a1',
       'a/test_db2.py::test_a2',
       'b/test_error.py::test_root',
       'failure_demo.py::TestCustomAssertMsg::test_custom_repr',
       'failure_demo.py::TestCustomAssertMsg::test_multiline',
       'failure_demo.py::TestCustomAssertMsg::test_single_line',
       'failure_demo.py::TestFailing::test_not',
       'failure_demo.py::TestFailing::test_simple',
       'failure_demo.py::TestFailing::test_simple_multiline',
       'failure_demo.py::TestMoreErrors::test_compare',
       'failure_demo.py::TestMoreErrors::test_complex_error',
       'failure_demo.py::TestMoreErrors::test_global_func',
       'failure_demo.py::TestMoreErrors::test_instance',
       'failure_demo.py::TestMoreErrors::test_startswith',
       'failure_demo.py::TestMoreErrors::test_startswith_nested',
       'failure_demo.py::TestMoreErrors::test_try_finally',
       'failure_demo.py::TestMoreErrors::test_z1_unpack_error',
       'failure_demo.py::TestMoreErrors::test_z2_type_error',
       'failure_demo.py::TestRaises::test_raise',
       'failure_demo.py::TestRaises::test_raises',
       'failure_demo.py::TestRaises::test_raises_doesnt',
       'failure_demo.py::TestRaises::test_reinterpret_fails_with_print_for_the_fun_of_it',
       'failure_demo.py::TestRaises::test_some_error',
       'failure_demo.py::TestRaises::test_tupleerror',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_attrs',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_dataclass',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_dict',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_list',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_list_long',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_long_text',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_long_text_multiline',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_longer_list',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_multiline_text',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_set',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_similar_text',
       'failure_demo.py::TestSpecialisedExplanations::test_eq_text',
       'failure_demo.py::TestSpecialisedExplanations::test_in_list',
       'failure_demo.py::TestSpecialisedExplanations::test_not_in_text_multiline',
       'failure_demo.py::TestSpecialisedExplanations::test_not_in_text_single',
       'failure_demo.py::TestSpecialisedExplanations::test_not_in_text_single_long',
       'failure_demo.py::TestSpecialisedExplanations::test_not_in_text_single_long_term',
       'failure_demo.py::test_attribute',
       'failure_demo.py::test_attribute_failure',
       'failure_demo.py::test_attribute_instance',
       'failure_demo.py::test_attribute_multiple',
       'failure_demo.py::test_dynamic_compile_shows_nicely',
       'failure_demo.py::test_generative[3-6]',
       'multipython.py::test_basic_objects[python3.5-python3.5-42]',
       'multipython.py::test_basic_objects[python3.5-python3.5-obj1]',
       'multipython.py::test_basic_objects[python3.5-python3.5-obj2]',
       'multipython.py::test_basic_objects[python3.5-python3.6-42]',
       'multipython.py::test_basic_objects[python3.5-python3.6-obj1]',
       'multipython.py::test_basic_objects[python3.5-python3.6-obj2]',
       'multipython.py::test_basic_objects[python3.5-python3.7-42]',
       'multipython.py::test_basic_objects[python3.5-python3.7-obj1]',
       'multipython.py::test_basic_objects[python3.5-python3.7-obj2]',
       'multipython.py::test_basic_objects[python3.6-python3.5-42]',
       'multipython.py::test_basic_objects[python3.6-python3.5-obj1]',
       'multipython.py::test_basic_objects[python3.6-python3.5-obj2]',
       'multipython.py::test_basic_objects[python3.6-python3.6-42]',
       'multipython.py::test_basic_objects[python3.6-python3.6-obj1]',
       'multipython.py::test_basic_objects[python3.6-python3.6-obj2]',
       'multipython.py::test_basic_objects[python3.6-python3.7-42]',
       'multipython.py::test_basic_objects[python3.6-python3.7-obj1]',
       'multipython.py::test_basic_objects[python3.6-python3.7-obj2]',
       'multipython.py::test_basic_objects[python3.7-python3.5-42]',
       'multipython.py::test_basic_objects[python3.7-python3.5-obj1]',
       'multipython.py::test_basic_objects[python3.7-python3.5-obj2]',
       'multipython.py::test_basic_objects[python3.7-python3.6-42]',
       'multipython.py::test_basic_objects[python3.7-python3.6-obj1]',
       'multipython.py::test_basic_objects[python3.7-python3.6-obj2]',
       'multipython.py::test_basic_objects[python3.7-python3.7-42]',
       'multipython.py::test_basic_objects[python3.7-python3.7-obj1]',
       'multipython.py::test_basic_objects[python3.7-python3.7-obj2]',
       'test_50.py::test_num[0]',
       'test_50.py::test_num[10]',
       'test_50.py::test_num[11]',
       'test_50.py::test_num[12]',
       'test_50.py::test_num[13]',
       'test_50.py::test_num[14]',
       'test_50.py::test_num[15]',
       'test_50.py::test_num[16]',
       'test_50.py::test_num[17]',
       'test_50.py::test_num[18]',
       'test_50.py::test_num[19]',
       'test_50.py::test_num[1]',
       'test_50.py::test_num[20]',
       'test_50.py::test_num[21]',
       'test_50.py::test_num[22]',
       'test_50.py::test_num[23]',
       'test_50.py::test_num[24]',
       'test_50.py::test_num[25]',
       'test_50.py::test_num[26]',
       'test_50.py::test_num[27]',
       'test_50.py::test_num[28]',
       'test_50.py::test_num[29]',
       'test_50.py::test_num[2]',
       'test_50.py::test_num[30]',
       'test_50.py::test_num[31]',
       'test_50.py::test_num[32]',
       'test_50.py::test_num[33]',
       'test_50.py::test_num[34]',
       'test_50.py::test_num[35]',
       'test_50.py::test_num[36]',
       'test_50.py::test_num[37]',
       'test_50.py::test_num[38]',
       'test_50.py::test_num[39]',
       'test_50.py::test_num[3]',
       'test_50.py::test_num[40]',
       'test_50.py::test_num[41]',
       'test_50.py::test_num[42]',
       'test_50.py::test_num[43]',
       'test_50.py::test_num[44]',
       'test_50.py::test_num[45]',
       'test_50.py::test_num[46]',
       'test_50.py::test_num[47]',
       'test_50.py::test_num[48]',
       'test_50.py::test_num[49]',
       'test_50.py::test_num[4]',
       'test_50.py::test_num[5]',
       'test_50.py::test_num[6]',
       'test_50.py::test_num[7]',
       'test_50.py::test_num[8]',
       'test_50.py::test_num[9]',
       'test_assert1.py::test_function',
       'test_assert2.py::test_set_comparison',
       'test_backends.py::test_db_initialized[d1]',
       'test_backends.py::test_db_initialized[d2]',
       'test_caching.py::test_function',
       'test_checkconfig.py::test_something',
       'test_class.py::TestClass::test_one',
       'test_class.py::TestClass::test_two',
       'test_class_demo.py::TestClassDemoInstance::test_one',
       'test_class_demo.py::TestClassDemoInstance::test_two',
       'test_compute.py::test_compute[0]',
       'test_compute.py::test_compute[1]',
       'test_compute.py::test_compute[2]',
       'test_compute.py::test_compute[3]',
       'test_compute.py::test_compute[4]',
       'test_custom_marker.py::test_with_args',
       'test_foocompare.py::test_compare',
       'test_indirect_list.py::test_indirect[a-b]',
       'test_mark_three_times.py::TestClass::test_something',
       'test_module.py::SomeTest::test_unit1',
       'test_module.py::TestHello::test_method1',
       'test_module.py::TestHello::test_method2',
       'test_module.py::TestOther::test_other',
       'test_module.py::test_call_fails',
       'test_module.py::test_event_simple',
       'test_module.py::test_fail1',
       'test_module.py::test_fail2',
       'test_module.py::test_func1[opt1]',
       'test_module.py::test_func1[opt2]',
       'test_module.py::test_func_fast',
       'test_module.py::test_func_slow',
       'test_module.py::test_interface_complex',
       'test_module.py::test_interface_simple',
       'test_module.py::test_setup_fails',
       'test_parametrize.py::TestClass::test_equals[1-2]',
       'test_parametrize.py::TestClass::test_equals[3-3]',
       'test_parametrize.py::TestClass::test_zerodivision[1-0]',
       'test_plat.py::test_if_apple_is_evil',
       'test_plat.py::test_if_linux_works',
       'test_plat.py::test_if_win32_crashes',
       'test_plat.py::test_runs_everywhere',
       'test_pytest_param_example.py::test_eval[1+7-8]',
       'test_pytest_param_example.py::test_eval[basic_2+4]',
       'test_pytest_param_example.py::test_eval[basic_6*9]',
       'test_sample.py::test_answer',
       'test_scenarios.py::TestSampleWithScenarios::test_demo1[advanced]',
       'test_scenarios.py::TestSampleWithScenarios::test_demo1[basic]',
       'test_scenarios.py::TestSampleWithScenarios::test_demo2[advanced]',
       'test_scenarios.py::TestSampleWithScenarios::test_demo2[basic]',
       'test_server.py::TestClass::test_method',
       'test_server.py::test_another',
       'test_server.py::test_send_http',
       'test_server.py::test_something_quick',
       'test_simple.yaml::hello',
       'test_simple.yaml::ok',
       'test_some_are_slow.py::test_funcfast',
       'test_some_are_slow.py::test_funcslow1',
       'test_some_are_slow.py::test_funcslow2',
       'test_someenv.py::test_basic_db_operation',
       'test_step.py::TestUserHandling::test_deletion',
       'test_step.py::TestUserHandling::test_login',
       'test_step.py::TestUserHandling::test_modification',
       'test_step.py::test_normal',
       'test_sysexit.py::test_mytest',
       'test_tmp_path.py::test_needsfiles']
    cache/stepwise contains:
      []
    example/value contains:
      42

    ========================== no tests ran in 0.12s ===========================

``--cache-show`` takes an optional argument to specify a glob pattern for
filtering:

.. code-block:: pytest

    $ pytest --cache-show example/*
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-7.x.y, py-1.x.y, pluggy-0.x.y
    cachedir: $PYTHON_PREFIX/.pytest_cache
    rootdir: $REGENDOC_TMPDIR
    cachedir: $PYTHON_PREFIX/.pytest_cache
    ----------------------- cache values for 'example/*' -----------------------
    example/value contains:
      42

    ========================== no tests ran in 0.12s ===========================

Clearing Cache content
----------------------

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
