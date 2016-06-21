.. _index: test discovery
.. _`testdirectory`:

Test directory structure
========================


``pytest`` supports two common test layouts:

* putting tests into an extra directory outside your actual application
  code, useful if you have many functional tests or for other reasons
  want to keep tests separate from actual application code (often a good
  idea)::

    setup.py   # your setuptools Python package metadata
    src/
        __init__.py
        appmodule.py
        module1/
            part1.py
            part2.py
        ...
    tests/
        test_appmodule.py
        module1/
            test_part1.py
            test_part2.py
        ...


* inlining test directories into your application package, useful if you
  have direct relation between (unit-)test and application modules and
  want to distribute your tests along with your application::

    setup.py   # your setuptools Python package metadata
    src/
        __init__.py
        appmodule.py
        tests/
            test_appmodule.py
        module1/
            part1.py
            part2.py
            tests/
                test_part1.py
                test_part2.py
        ...


Typically you can run tests by pointing to test directories or modules::

    pytest tests/test_appmodule.py      # for external test dirs
    pytest src/tests/test_appmodule.py  # for inlined test dirs
    pytest src                          # run tests in all below test directories
    pytest                              # run all tests below current dir
    ...


You shouldn't have ``__init__.py`` files in your test directories.
