.. _`parametrizebasic`:

Repeating tests with parametrize
================================

pytest support test parametrization using a builtin ``pytest.mark.parametrize``
decorator, which enables parametrization of arguments for a test function.

Here is a typical example of a test function that implements checking that a
certain input leads to an expected output::

    # content of test_expectation.py
    import pytest
    @pytest.mark.parametrize("test_input,expected", [
        ("3+5", 8),
        ("2+4", 6),
        ("6*9", 42),
    ])
    def test_eval(test_input, expected):
        assert eval(test_input) == expected

Here, the ``@pytest.mark.parametrize`` decorator defines three different
``(test_input,expected)`` tuples so that the ``test_eval`` function will run
three times using them in turn. Note that the test arguments must match the
comma-separated values provided in the decorator::

    $ py.test
    ======= test session starts ========
    platform linux -- Python 3.5.1, pytest-2.9.2, py-1.4.31, pluggy-0.3.1
    rootdir: $REGENDOC_TMPDIR, inifile:
    collected 3 items

    test_expectation.py ..F

    ======= FAILURES ========
    _______ test_eval[6*9-42] ________

    test_input = '6*9', expected = 42

        @pytest.mark.parametrize("test_input,expected", [
            ("3+5", 8),
            ("2+4", 6),
            ("6*9", 42),
        ])
        def test_eval(test_input, expected):
    >       assert eval(test_input) == expected
    E       assert 54 == 42
    E        +  where 54 = eval('6*9')

    test_expectation.py:8: AssertionError
    ======= 1 failed, 2 passed in 0.12 seconds ========

As designed in this example, only one pair of input/output values fails
the simple test function.  And as usual with test function arguments,
you can see the ``test_input`` and ``expected`` values in the traceback.

See also
--------

* ADVANCED parametrize
