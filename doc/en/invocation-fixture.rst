.. _invocation_scoped_fixture:

Invocation-scoped fixtures
==========================

.. versionadded:: 3.0

.. note::
    This feature is experimental, so if decided that it brings too much problems
    or considered too complicated it might be removed in pytest ``3.1``.

Fixtures can be defined with ``invocation`` scope, meaning that the fixture
can be requested by fixtures from any scope, but when they do they assume
the same scope as the fixture requesting it.

An ``invocation``-scoped fixture can be requested from different scopes
in the same test session, in which case each scope will have its own copy.

Example
-------

Consider a fixture which manages external process execution:
this fixture provides auxiliary methods for tests and fixtures to start external
processes while making sure the
processes terminate at the appropriate time. Because it makes sense
to start a webserver for the entire session and also to execute a numerical
simulation for a single test function, the ``process_manager``
fixture can be declared as ``invocation``, so each scope gets its own
value and can manage processes which will live for the duration of the scope.

.. code-block:: python

    import pytest

    @pytest.fixture(scope='invocation')
    def process_manager():
        """
        Return a ProcessManager instance which can be used to start
        long-lived processes and ensures they are terminated at the
        appropriate scope.
        """
        m = ProcessManager()
        yield m
        m.shutdown_all()


    @pytest.fixture(scope='session')
    def server(process_manager):
        process_manager.start(sys.executable, 'server.py')


    @pytest.fixture(scope='function')
    def start_simulation(process_manager):
        import functools
        return functools.partial(process_manager.start,
                                 sys.executable, 'simulator.py')


In the above code, simulators started using ``start_simulation`` will be
terminated when the test function exits, while the server will be kept
active for the entire simulation run, being terminated when the test session
finishes.

