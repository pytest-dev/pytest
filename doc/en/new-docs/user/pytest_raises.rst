.. _index: exceptions, pytest.raises
.. _`pytestraises`:

Asserting about exceptions with pytest.raises
=============================================

An important aspect of unit testing is checking boundary/edge cases, and behaviour in the case of unexpected input. If you have a function that in some cases raises an exception, you can confirm this is working as expected using a context manager called ``pytest.raises``. Example::

    import pytest

    def test_zero_division():
        with pytest.raises(ZeroDivisionError):
            1 / 0


If an exception is not raised in a ``pytest.raises`` block, the test will fail.  Example::

    import pytest

    def test_zero_division():
        with pytest.raises(ZeroDivisionError):
            2 / 1


Running this will give the result::

    _______________________ test_zero_division ____________________________

        def test_zero_division():
            with pytest.raises(ZeroDivisionError):
    >           2 / 1
    E           Failed: DID NOT RAISE


A related concept is that of making a test as "expected to fail", or xfail (TODO-User-xfail).
