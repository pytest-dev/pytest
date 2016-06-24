.. _`commandlineuseful`:

Most useful command-line options
================================

Direct argument to select tests

-s, --capture=no
----------------

Normally stdout is only showed for failing tests. ``-s`` shows stdout calls, for example the print statement of all the tests.

An example of how that works can be the following one:
If the following piece of code, saved in a file named ``test_documentation.py`` is run with no parameter (if you run in the terminal, ``py.test test_documentation.py``).::

  def test_fail():
      print "this test is going to fail"
      assert False


  def test_pass():
      print "this test is going to pass"
      assert True

What will be printed will in the terminal be the following::

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

But if it is run with the parameter (``py.test test_documentation.py -s``), the result showed will be the following one::

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

The biggest difference in the both statements is the part entitled "Tests session starts", where it prints the statements "this test is going to pass" (so the test that passed), and the "this test is going to fail".

-k EXPRESSION
-------------

EXPRESSION is a key word to select a subset of tests to be run.

An example of this using the same file as above could be the following one:
if this file is run without the parameter (if you run in the terminal, ``py.test test_documentation.py``), both tests on the file would be run. If you run that with the parameter (typing, for example ``py.test test_documentation.py -k pass``), it would filter only the tests names that contains the expression 'pass', so it would run only the test_pass().

-v, --verbose
-------------
It shows more details of the tests, for example the test names.

--collect-only
--------------
Shows a list of the tests without running them. It can be useful in combination with ``-k``.

for example, in the test file above, if it was run with the collect-only argument, it would display as a result something like the bellow file:

  collected 2 items
  <Module 'test_documentation.py'>
    <Function 'test_fail'>
    <Function 'test_pass'>
  =========================================================================== no tests ran in 0.00 seconds ======================

-x, --exitfirst
---------------
Exit instantly after the first failure.

For example, in the test file above, if it is run with the --exitfirst argument, it would run only the ``test_fail``, and not the ``test_pass``, because it would exit after having the first failure.

--lf, --last-failed
-------------------
Runs only the set of tests that failed at the last run, or all tests if none failed.

For example, in the test file above, if it is run first without any arguments, and after with the --last-failed argument, only the set of tests that failed would run, in this example, only the ``test_fail()`` would be executed.

-h, --help
----------
Shows a list with all command options.

See also command line options reference [TO-DO]
