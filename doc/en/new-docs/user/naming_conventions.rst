.. _index: test discovery, naming

.. _`namingconventions`:

Naming conventions and test discovery
=====================================

When you run ``pytest``, by default it will look for tests in all directories and files below the current directory.

You can specify one or more paths and then pytest will look in those paths instead. For example::


    $ pytest src/modules/example/test/


File names should start or end with "test", as in ``test_example.py`` or ``example_test.py``.

If tests are defined as methods on a class, the class name should start with "Test", as in  ``TestExample``. The class should not have an ``__init__`` method.

Test method names or function names should start with "test_", as in ``test_example``. Methods with names that don't match this pattern won't be executed as tests.

Calling ``pytest --collect-only`` is a useful way to see what tests pytest will discover, without actually running the tests.


To find out more about running unittest or nose tests, see TODO(Advanced - running unittest/nose)

To change where pytest looks for tests by default, see TODO(Advanced - conftest/ini config)

To change how pytest recognises tests by name, see TODO(Advanced - configuring test discovery).



