
Monkeypatching/mocking modules and environments
================================================================

.. currentmodule:: _pytest.monkeypatch

Sometimes tests need to invoke functionality which depends
on global settings or which invokes code which cannot be easily
tested such as network access.  The ``monkeypatch`` fixture
helps you to safely set/delete an attribute, dictionary item or
environment variable or to modify ``sys.path`` for importing.
See the `monkeypatch blog post`_ for some introduction material
and a discussion of its motivation.

.. _`monkeypatch blog post`: http://tetamap.wordpress.com/2009/03/03/monkeypatching-in-unit-tests-done-right/


Simple example: monkeypatching functions
---------------------------------------------------

If you want to pretend that ``os.expanduser`` returns a certain
directory, you can use the :py:meth:`monkeypatch.setattr` method to
patch this function before calling into a function which uses it::

    # content of test_module.py
    import os.path
    def getssh(): # pseudo application code
        return os.path.join(os.path.expanduser("~admin"), '.ssh')

    def test_mytest(monkeypatch):
        def mockreturn(path):
            return '/abc'
        monkeypatch.setattr(os.path, 'expanduser', mockreturn)
        x = getssh()
        assert x == '/abc/.ssh'

Here our test function monkeypatches ``os.path.expanduser`` and
then calls into an function that calls it.  After the test function 
finishes the ``os.path.expanduser`` modification will be undone.

example: preventing "requests" from remote operations
------------------------------------------------------

If you want to prevent the "requests" library from performing http
requests in all your tests, you can do::

    # content of conftest.py
    import pytest
    @pytest.fixture(autouse=True)
    def no_requests(monkeypatch):
        monkeypatch.delattr("requests.sessions.Session.request")

This autouse fixture will be executed for each test function and it
will delete the method ``request.session.Session.request`` 
so that any attempts within tests to create http requests will fail.

example: setting an environment variable for the test session
-------------------------------------------------------------

If you would like for an environment variable to be
configured for the entire test session, you can add this to your
top-level ``conftest.py`` file:

.. code-block:: python

    # content of conftest.py
    @pytest.fixture(scope='session', autouse=True)
    def enable_debugging(monkeypatch):
        monkeypatch.setenv("DEBUGGING_VERBOSITY", "4")

This auto-use fixture will set the ``DEBUGGING_VERBOSITY`` environment variable for
the entire test session.

Note that the ability to use a ``monkeypatch`` fixture from a ``session``-scoped
fixture was added in pytest-3.0.


Method reference of the monkeypatch fixture
-------------------------------------------

.. autoclass:: MonkeyPatch
    :members: setattr, replace, delattr, setitem, delitem, setenv, delenv, syspath_prepend, chdir, undo

``monkeypatch.setattr/delattr/delitem/delenv()`` all
by default raise an Exception if the target does not exist.
Pass ``raising=False`` if you want to skip this check.

