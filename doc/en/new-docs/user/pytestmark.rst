.. _index: mark
.. _`pytestmarkbasic`:

Grouping tests with pytest.mark
===============================

The ``pytest.mark`` decorator can be used to add metadata to tests. This is useful to note related tests and to select groups of tests to be run. In the following example, only one test has the mark "webtest"::

    # content of test_server.py

    import pytest

    @pytest.mark.webtest
    def test_send_http():
        pass # perform some webtest test for your app

    def test_something_quick():
        pass

    def test_another():
        pass


    class TestClass:
        def test_method(self):
            pass


You can then restrict a test run to only run tests marked with ``webtest`` by using the "-m" command line option::

    $ py.test -v -m webtest
    ======= test session starts ========
    platform linux -- Python 3.5.1, pytest-2.9.2, py-1.4.31, pluggy-0.3.1 -- $PYTHON_PREFIX/bin/python3.5
    cachedir: .cache
    rootdir: $REGENDOC_TMPDIR, inifile: 
    collecting ... collected 4 items
    
    test_server.py::test_send_http PASSED
    
    ======= 3 tests deselected by "-m 'webtest'" ========
    ======= 1 passed, 3 deselected in 0.12 seconds ========

Or the inverse, running all tests except the webtest ones::

    $ py.test -v -m "not webtest"
    ======= test session starts ========
    platform linux -- Python 3.5.1, pytest-2.9.2, py-1.4.31, pluggy-0.3.1 -- $PYTHON_PREFIX/bin/python3.5
    cachedir: .cache
    rootdir: $REGENDOC_TMPDIR, inifile: 
    collecting ... collected 4 items
    
    test_server.py::test_something_quick PASSED
    test_server.py::test_another PASSED
    test_server.py::TestClass::test_method PASSED
    
    ======= 1 tests deselected by "-m 'not webtest'" ========
    ======= 3 passed, 1 deselected in 0.12 seconds ========


You may use ``pytest.mark`` decorators with classes to apply markers to all of
its test methods::

    # content of test_mark_classlevel.py

    import pytest

    @pytest.mark.webtest
    class TestClass:
        def test_startup(self):
            pass

        def test_startup_and_more(self):
            pass

This is equivalent to directly applying the decorator to the
two test functions.



Some built-in markers offer extra functionality instead of grouping tests, for example:

* :ref:`skipif <skipif??>` - skip a test function if a certain condition is met
* :ref:`xfail <xfail??>` - produce an "expected failure" outcome if a certain
  condition is met
* :ref:`parametrize <parametrizemark??>` to perform multiple calls
  to the same test function

See also 

* TODO (Basic - useful command line options)
* TODO(Advanced - adding extra functionality to marks)
* TODO (Advanced - ini - registering markers)
* TODO (Plugin author - adding a custom marker from a plugin)
