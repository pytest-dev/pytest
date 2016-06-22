.. _index: xfail
.. _`xfailbasic`:

Xfail - expecting a test to fail
================================

You can use the ``xfail`` marker to indicate that you expect a test to fail.
One common use-case for this is when you find a bug in your software and you
write a test to document how the software *should* behave. This test will of
course fail until you fix the bug. To avoid having a failing test you mark the
test as ``xfail``. Once the bug is fixed you remove the ``xfail`` marker and
have a regression test which ensures that the bug will not reccur.

A related concept is skipping. If your test should be skipped under certain
circumstances (e.g. only runs on Windows) then use the ``skipif`` marker. A
skipped test is not executed whereas an ``xfail`` test by default will. TODO
link skipping.

.. code-block:: python

    @pytest.mark.xfail
    def test_function():
        ...

Having the ``xfail`` marker will still run the test but won't report a
traceback once it fails. Instead terminal reporting will list it in the
"expected to fail" (``XFAIL``) section. If the test doesn't fail it will be
reported as "unexpectedly passing" (``XPASS``).

``strict`` parameter
~~~~~~~~~~~~~~~~~~~~

We recommend you always set ``strict=True`` to ensure ``XPASS`` (unexpectedly
passing) causes the tests to be recorded as a failure.  The reason is if you
mark a test as ``xfail`` you actually expect it to fail.  If it suddenly passes
maybe someone fixed the bug, or perphaps the test is not doing what you think
it is. This especially has implications for continuous integration systems,
which usually only have representations for PASS (green) and FAIL (red),
not XPASS or XFAIL.

``XPASS`` doesn't fail the test suite, unless the ``strict`` keyword-only
parameter is passed as ``True`` (default is ``False``):

.. code-block:: python

    @pytest.mark.xfail(strict=True)
    def test_function():
        ...


This will make ``XPASS`` ("unexpectedly passing") results from this test to
fail the test suite.

You can change the default value of the ``strict`` parameter using the
``xfail_strict`` ini option:

.. code-block:: ini

    [pytest]
    xfail_strict=true

TODO Link more information about ini files


See also
--------

* Types of test result
* Skipping
* pytest raises
* flaky tests
* ADVANCED xfail
