.. _index: skip, skipif
.. _`skippingbasic`:

Skipping
========

If your software runs on multiple platforms, or supports multiple versions of
different dependencies, it is likely that you will encounter bugs or strange
edge cases that only occur in one particular environment. In this case, it can
be useful to write a test for that should only be exercised on that
environment, and in other cases it doesn't need to be run - it can be skipped.

If you wish to skip something conditionally then you can use ``skipif`` instead.
Here is an example of marking a test function to be skipped when run on a
Python 2 interpreter::

    import sys
    @pytest.mark.skipif(sys.version_info < (3, 0),
                        reason="requires Python3")
    def test_function():
        ...

During test function setup the condition ("sys.version_info >= (3, 0)") is
checked.  If it evaluates to True, the test function will be skipped with the
specified reason.  Note that pytest enforces specifying a reason in order to
report meaningful "skip reasons" (e.g. when using the command line options
``-rs``).  If the condition is a string, it will be evaluated as python
expression.

Example output::

    $ py.test -rs
    ======= test session starts ========
    platform linux -- Python 3.5.1, pytest-2.9.2, py-1.4.31, pluggy-0.3.1
    rootdir: $REGENDOC_TMPDIR, inifile: 
    collected 1 items
    
    test_function.py s
    ======= short test summary info ========    
    SKIP [1] test_function.py:4: requires Python3
    ======= 1 skipped in 0.01 seconds ========    



Re-using skipif decorators
--------------------------

You can also define the decorator once and re-use it::

    import sys
    python3_only = pytest.mark.skipif(sys.version_info < (3, 0),
                                      reason="requires Python3")
    @python3_only
    def test_function1():
        ...
    
    @python3_only
    def test_function2():
        ...
    
    @python3_only
    def test_function3():
        ...

For larger test suites it's usually a good idea to have one file where you
define the markers which you then consistently apply throughout your test
suite.


Unconditional skip
------------------

To skip a test without a condition use the ``pytest.mark.skip`` decorator which
may be passed an optional ``reason``:

.. code-block:: python

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_the_unknown():
        ...

If you are skipping a test because it fails (e.g. a bug in your software that
you want to track) the ``xfail`` marker is probably more appropiate.


See also
--------

* Test results page
* xfail
