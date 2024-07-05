.. _`Pytest in CI pipelines`:

Pytest in CI pipelines
=================================================

Rationale
---------

The goal of testing in a CI pipeline is different from testing locally. Indeed,
you can quickly edit some code and run your tests again on your computer, but
it is not possible with CI pipeline. They run on a separate server and are
triggered by specific actions.

From that observation, pytest can detect when it is in a CI environment and
adapt some of its behaviours.

How CI is detected
------------------

Pytest knows it is in a CI environment when one of the two environment variables
`CI` or `BUILD_NUMBER` is set, regardless of their value.

Effects on CI
-------------

For now, the effects on pytest of being in a CI environment are limited. When a
CI environment is detected:

- the output of the short test summary info is no longer truncated to the terminal
  size i.e. the entire message will be shown.

.. code-block:: python

    # content of test_ci.py

    import pytest


    def test_db_initialized():
        pytest.fail(
            "deliberately failing for demo purpose, Lorem ipsum dolor sit amet, "
            "consectetur adipiscing elit. Cras facilisis, massa in suscipit "
            "dignissim, mauris lacus molestie nisi, quis varius metus nulla ut ipsum."
        )


.. code-block:: pytest
    // in a local environment (based on your terminal width)
    $ pytest test_ci.py
    ...
    ========================= short test summary info ==========================
    FAILED test_backends.py::test_db_initialized[d2] - Failed: deliberately f...

    // in a CI environment
    $ export CI=true
    $ pytest test_ci.py
    ...
    ========================= short test summary info ==========================
    FAILED test_backends.py::test_db_initialized[d2] - Failed: deliberately failing
    for demo purpose, Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras
    facilisis, massa in suscipit dignissim, mauris lacus molestie nisi, quis varius
    metus nulla ut ipsum.
