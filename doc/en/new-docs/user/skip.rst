.. _index: skip
.. _`skipping`:

Skip and skipif
===============

If your software runs on multiple platforms, or supports multiple versions of different dependencies, it is likely that you will encounter bugs or strange edge cases that only occur in one particular environment. In this case, it can be useful to write a test for that should only be exercised on that environment, and in other cases it doesn't need to be run - it can be skipped.


