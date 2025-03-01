.. _types:

Typing in pytest
================

.. note::
    This page assumes the reader is familiar with Python's typing system and its advantages.

    For more information, refer to `Python's Typing Documentation <https://docs.python.org/3/library/typing.html>`_.

Why type tests?
---------------

Typing tests provides significant advantages:

- **Readability:** Clearly defines expected inputs and outputs, improving readability, especially in complex or parameterized tests.

- **Refactoring:** This is the main benefit in typing tests, as it will greatly help with refactoring, letting the type checker point out the necessary changes in both production and tests, without needing to run the full test suite.

For production code, typing also helps catching some bugs that might not be caught by tests at all (regardless of coverage), for example:

.. code-block:: python

    def get_caption(target: int, items: list[tuple[int, str]]) -> str:
        for value, caption in items:
            if value == target:
                return caption


The type checker will correctly error out that the function might return `None`, however even a full coverage test suite might miss that case:

.. code-block:: python

    def test_get_caption() -> None:
        assert get_caption(10, [(1, "foo"), (10, "bar")]) == "bar"


Note the code above has 100% coverage, but the bug is not caught (of course the example is "obvious", but serves to illustrate the point).



Using typing in test suites
---------------------------

To type fixtures in pytest, just add normal types to the fixture functions -- there is nothing special that needs to be done just because of the `fixture` decorator.

.. code-block:: python

    import pytest


    @pytest.fixture
    def sample_fixture() -> int:
        return 38

In the same manner, the fixtures passed to test functions need be annotated with the fixture's return type:

.. code-block:: python

    def test_sample_fixture(sample_fixture: int) -> None:
        assert sample_fixture == 38

From the POV of the type checker, it does not matter that `sample_fixture` is actually a fixture managed by pytest, all it matters to it is that `sample_fixture` is a parameter of type `int`.


The same logic applies to :ref:`@pytest.mark.parametrize <@pytest.mark.parametrize>`:

.. code-block:: python


    @pytest.mark.parametrize("input_value, expected_output", [(1, 2), (5, 6), (10, 11)])
    def test_increment(input_value: int, expected_output: int) -> None:
        assert input_value + 1 == expected_output


The same logic applies when typing fixture functions which receive other fixtures:

.. code-block:: python

    @pytest.fixture
    def mock_env_user(monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("USER", "TestingUser")


Conclusion
----------

Incorporating typing into pytest tests enhances **clarity**, improves **debugging** and **maintenance**, and ensures **type safety**.
These practices lead to a **robust**, **readable**, and **easily maintainable** test suite that is better equipped to handle future changes with minimal risk of errors.
