.. index:: assert

.. _`assertstatements`:

Assert statements
=================

Assert statements are at the core of what a test is. For unit tests, each test function or method should have one and only one assert statement.

The general idea is to set up the required input data, call a function or method from the source code, and then confirm (by assert statements) that the result conforms to expectations.

The plain Python assert statement can be used. By default it doesn't provide very useful information when an assertion fails, but pytest will expand the output to give more context.

An example::

    # contents of source code

    def vowels():
        return set('aeiou')


    # content of test_language.py

    def test_vowels():
        result =  vowels()
        expected = set('aeyou')
        assert result == expected


If we run this test file::


    $ py.test test_language.py
    ======= test session starts ========
    platform linux -- Python 3.5.1, pytest-2.9.2, py-1.4.31, pluggy-0.3.1
    rootdir: $REGENDOC_TMPDIR, inifile: 
    collected 1 items
    
    test_language.py F
    
    ======= FAILURES ========
    _______ test_vowels ________

        def test_vowels():
            result =  vowels()
            expected = set('aeyou')
    >       assert result == expected
    E       assert set(['a', 'e', 'i', 'o', 'u']) == set(['a', 'e', 'o', 'u', 'y'])
    E         Extra items in the left set:
    E         'i'
    E         Extra items in the right set:
    E         'y'
    E         Use -v to get the full diff

    
    test_language.py:5: AssertionError
    ======= 1 failed in 0.12 seconds ========


Pytest output shows exactly where the test failed, and how the two pieces of data being compared differ. This is helpful to quickly resolve a failing test.


To find out more on making assertions about numbers and arrays, see TODO(Advanced - number and numpy testing). To find out more about how pytest gives extra context to assert statements, see TODO(Contributor guide - assert rewriting).
