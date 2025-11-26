.. _subtests:

How to use subtests
===================

.. versionadded:: 9.0

.. note::

    This feature is experimental. Its behavior, particularly how failures are reported, may evolve in future releases. However, the core functionality and usage are considered stable.

pytest allows for grouping assertions within a normal test, known as *subtests*.

Subtests are an alternative to parametrization, particularly useful when the exact parametrization values are not known at collection time.


.. code-block:: python

    # content of test_subtest.py


    def test(subtests):
        for i in range(5):
            with subtests.test(msg="custom message", i=i):
                assert i % 2 == 0

Each assertion failure or error is caught by the context manager and reported individually:

.. code-block:: pytest

    $ pytest -q test_subtest.py
    uuuuuF                                                               [100%]
    ================================= FAILURES =================================
    _______________________ test [custom message] (i=1) ________________________

    subtests = <_pytest.subtests.Subtests object at 0xdeadbeef0001>

        def test(subtests):
            for i in range(5):
                with subtests.test(msg="custom message", i=i):
    >               assert i % 2 == 0
    E               assert (1 % 2) == 0

    test_subtest.py:6: AssertionError
    _______________________ test [custom message] (i=3) ________________________

    subtests = <_pytest.subtests.Subtests object at 0xdeadbeef0001>

        def test(subtests):
            for i in range(5):
                with subtests.test(msg="custom message", i=i):
    >               assert i % 2 == 0
    E               assert (3 % 2) == 0

    test_subtest.py:6: AssertionError
    ___________________________________ test ___________________________________
    contains 2 failed subtests
    ========================= short test summary info ==========================
    SUBFAILED[custom message] (i=1) test_subtest.py::test - assert (1 % 2) == 0
    SUBFAILED[custom message] (i=3) test_subtest.py::test - assert (3 % 2) == 0
    FAILED test_subtest.py::test - contains 2 failed subtests
    3 failed, 3 subtests passed in 0.12s

In the output above:

* Subtest failures are reported as ``SUBFAILED``.
* Subtests are reported first and the "top-level" test is reported at the end on its own.

Note that it is possible to use ``subtests`` multiple times in the same test, or even mix and match with normal assertions
outside the ``subtests.test`` block:

.. code-block:: python

    def test(subtests):
        for i in range(5):
            with subtests.test("stage 1", i=i):
                assert i % 2 == 0

        assert func() == 10

        for i in range(10, 20):
            with subtests.test("stage 2", i=i):
                assert i % 2 == 0

.. note::

    See :ref:`parametrize` for an alternative to subtests.


Verbosity
---------

By default, only **subtest failures** are shown. Higher verbosity levels (:option:`-v`) will also show progress output for **passed** subtests.

It is possible to control the verbosity of subtests by setting :confval:`verbosity_subtests`.


Typing
------

:class:`pytest.Subtests` is exported so it can be used in type annotations:

.. code-block:: python

    def test(subtests: pytest.Subtests) -> None: ...

.. _parametrize_vs_subtests:

Parametrization vs Subtests
---------------------------

While :ref:`traditional pytest parametrization <parametrize>` and ``subtests`` are similar, they have important differences and use cases.


Parametrization
~~~~~~~~~~~~~~~

* Happens at collection time.
* Generates individual tests.
* Parametrized tests can be referenced from the command line.
* Plays well with plugins that handle test execution, such as :option:`--last-failed`.
* Ideal for decision table testing.

Subtests
~~~~~~~~

* Happen during test execution.
* Are not known at collection time.
* Can be generated dynamically.
* Cannot be referenced individually from the command line.
* Plugins that handle test execution cannot target individual subtests.
* An assertion failure inside a subtest does not interrupt the test, letting users see all failures in the same report.


.. note::

    This feature was originally implemented as a separate plugin in `pytest-subtests <https://github.com/pytest-dev/pytest-subtests>`__, but since ``9.0`` has been merged into the core.

    The core implementation should be compatible to the plugin implementation, except it does not contain custom command-line options to control subtest output.
