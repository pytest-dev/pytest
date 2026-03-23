.. _`dynamic session-scoped fixtures`:

Building dynamic session-scoped parametrized fixtures
------------------------------------------------------

Sometimes you need a session-scoped fixture whose ``params`` depend on
command-line arguments or other runtime configuration that isn't available
when ``conftest.py`` is first imported.  A plain ``@pytest.fixture`` definition
cannot do this, because fixture ``params`` are evaluated at import time, before
:func:`pytest_configure` runs.

The solution is to register a *plugin class* containing the fixture inside
:func:`pytest_configure`.  At that point the command-line options have already
been parsed, so you can build the ``params`` list dynamically.

.. code-block:: python

    # content of conftest.py

    import pytest


    def pytest_addoption(parser):
        parser.addoption(
            "--servers",
            default="localhost",
            help="Comma-delimited list of servers to run tests against.",
        )


    def pytest_configure(config):
        # Options are available here, after argument parsing.
        server_list = [s.strip() for s in config.getoption("--servers").split(",")]

        class DynamicFixturePlugin:
            @pytest.fixture(scope="session", params=server_list)
            def server_hostname(self, request):
                """Parametrized session-scoped fixture built from --servers."""
                return request.param

        config.pluginmanager.register(DynamicFixturePlugin(), "server-hostname-fixture")

Now any test that requests ``server_hostname`` will be run once per server:

.. code-block:: python

    # content of test_servers.py


    def test_responds(server_hostname):
        assert server_hostname  # replace with real connection logic

Running with the default (one server):

.. code-block:: pytest

    $ pytest -q test_servers.py
    .
    1 passed in 0.12s

Running against multiple servers:

.. code-block:: pytest

    $ pytest -q test_servers.py --servers=host1,host2
    ..
    2 passed in 0.12s

.. note::

    The plugin class can contain multiple fixtures.  Each fixture defined on the
    class is treated exactly like a fixture in ``conftest.py`` — the ``self``
    parameter is the plugin instance and is not passed to the test.

A session-fixture which can look at all collected tests
-------------------------------------------------------

A session-scoped fixture effectively has access to all
collected test items.  Here is an example of a fixture
function which walks all collected tests and looks
if their test class defines a ``callme`` method and
calls it:

.. code-block:: python

    # content of conftest.py

    import pytest


    @pytest.fixture(scope="session", autouse=True)
    def callattr_ahead_of_alltests(request):
        print("callattr_ahead_of_alltests called")
        seen = {None}
        session = request.node
        for item in session.items:
            cls = item.getparent(pytest.Class)
            if cls not in seen:
                if hasattr(cls.obj, "callme"):
                    cls.obj.callme()
                seen.add(cls)

test classes may now define a ``callme`` method which
will be called ahead of running any tests:

.. code-block:: python

    # content of test_module.py


    class TestHello:
        @classmethod
        def callme(cls):
            print("callme called!")

        def test_method1(self):
            print("test_method1 called")

        def test_method2(self):
            print("test_method2 called")


    class TestOther:
        @classmethod
        def callme(cls):
            print("callme other called")

        def test_other(self):
            print("test other")


    # works with unittest as well ...
    import unittest


    class SomeTest(unittest.TestCase):
        @classmethod
        def callme(self):
            print("SomeTest callme called")

        def test_unit1(self):
            print("test_unit1 method called")

If you run this without output capturing:

.. code-block:: pytest

    $ pytest -q -s test_module.py
    callattr_ahead_of_alltests called
    callme called!
    callme other called
    SomeTest callme called
    test_method1 called
    .test_method2 called
    .test other
    .test_unit1 method called
    .
    4 passed in 0.12s
