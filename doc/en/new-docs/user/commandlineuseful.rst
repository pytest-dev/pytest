.. _`commandlineuseful`:

Most useful command-line options
================================

Direct argument to select tests

-s, --capture=no
----------------

Normally stdout and stderr are captured and only shown for failing tests.
The ``-s`` option can be used to disable capturing, showing stdcalls
for print statements, logging calls, etc.

Consider the following code and pytest execution:

.. code-block:: python

  # file test_documentation.py
  def test_fail():
      print "this test is going to fail"
      assert False


  def test_pass():
      print "this test is going to pass"
      assert True


::

    $ pytest
    test_documentation.py .F

    =================================== FAILURES ===================================
    __________________________________ test_fail ___________________________________

      def test_fail():
          print "this test is going to fail"
    >       assert False
    E       assert False

    test_documentation.py:7: AssertionError
    ----------------------------- Captured stdout call -----------------------------
    this test is going to fail
    ====================== 1 failed, 1 passed in 0.02 seconds ======================

You can see that no ``print`` statement is displayed, except for the failing test.

Now with the ``-s`` option::

    $ pytest -s
    ====================================================== test session starts ======================================================
    test_documentation.py this test is going to fail
    F this test is going to pass
    .

    =========================================================== FAILURES ============================================================
    ___________________________________________________________ test_fail ___________________________________________________________

      def test_fail():
          print "this test is going to fail"
    >       assert False
    E       assert False

    test_documentation.py:7: AssertionError
    ============================================== 1 failed, 1 passed in 0.02 seconds ===============================================

You can see that no output is captured, and ``print`` statements are displayed normally.

-k EXPRESSION
-------------

EXPRESSION is a keyword to select a subset of tests to be run.

Using the same file from the previous exception as an example, you can use::

    $ pytest -k pass


To filter only test names that contains ``pass``, so only ``test_pass()`` is executed.


-v, --verbose
-------------

Enables verbose mode, displaying full test names instead of only ``.`` in the
terminal::

    $ pytest -v
    =========================== test session starts ================================
    collected 2 items

    test_documentation.py::test_pass PASSED
    test_documentation.py::test_fail FAILED

    ================================= FAILURES =====================================
    ________________________________ test_fail _____________________________________

    def test_fail():
        print "this test is going to fail"
    >       assert False
    E       assert False

    test_documentation.py:7: AssertionError
    ------------------------------------------------------------------------------- Captured stdout call --------------------------------------------------------------------------------
    this test is going to fail
    ====================== 1 failed, 1 passed in 0.03 seconds ======================



--collect-only
--------------

Shows a list of the tests without running them

for example, in the test file above, if it was run with the collect-only argument, it would display as a result something like the bellow file::

    $ pytest --collect-only
      collected 2 items
      <Module 'test_documentation.py'>
        <Function 'test_fail'>
        <Function 'test_pass'>
    ====================== no tests ran in 0.00 seconds ======================

Note that ``--collect-only`` can be used with ``-k`` to see which tests are selected
by the expression.

-x, --exitfirst
---------------

Exit instantly after the first failure.

Using the previous file as an example, running with ``--exitfirst`` will only
execute up to ``test_fail``, and not the ``test_pass``, because it would exit after having the first failure.

--lf, --last-failed
-------------------

Runs only the set of tests that failed at the last run, or all tests if none failed.

For example, in the test file above, if it is run first without any arguments, and after with the --last-failed argument, only the set of tests that failed would run, in this example, only the ``test_fail()`` would be executed.

-h, --help
----------

Shows a list with all command options.

