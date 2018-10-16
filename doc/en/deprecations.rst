.. _deprecations:

Deprecations and Removals
=========================

This page lists all pytest features that are currently deprecated or have been removed in past major releases.
The objective is to give users a clear rationale why a certain feature has been removed, and what alternatives
should be used instead.

Deprecated Features
-------------------

Below is a complete list of all pytest features which are considered deprecated. Using those features will issue
:class:`_pytest.warning_types.PytestWarning` or subclasses, which can be filtered using
:ref:`standard warning filters <warnings>`.

Internal classes accessed through ``Node``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.9

Access of ``Module``, ``Function``, ``Class``, ``Instance``, ``File`` and ``Item`` through ``Node`` instances now issue
this warning::

    usage of Function.Module is deprecated, please use pytest.Module instead

Users should just ``import pytest`` and access those objects using the ``pytest`` module.

This has been documented as deprecated for years, but only now we are actually emitting deprecation warnings.

``cached_setup``
~~~~~~~~~~~~~~~~

.. deprecated:: 3.9

``request.cached_setup`` was the precursor of the setup/teardown mechanism available to fixtures.

Example:

.. code-block:: python

    @pytest.fixture
    def db_session():
        return request.cached_setup(
            setup=Session.create, teardown=lambda session: session.close(), scope="module"
        )

This should be updated to make use of standard fixture mechanisms:

.. code-block:: python

    @pytest.fixture(scope="module")
    def db_session():
        session = Session.create()
        yield session
        session.close()


You can consult `funcarg comparision section in the docs <https://docs.pytest.org/en/latest/funcarg_compare.html>`_ for
more information.

This has been documented as deprecated for years, but only now we are actually emitting deprecation warnings.


Using ``Class`` in custom Collectors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.9

Using objects named ``"Class"`` as a way to customize the type of nodes that are collected in ``Collector``
subclasses has been deprecated. Users instead should use ``pytest_collect_make_item`` to customize node types during
collection.

This issue should affect only advanced plugins who create new collection types, so if you see this warning
message please contact the authors so they can change the code.


``Config.warn`` and ``Node.warn``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.8

Those methods were part of the internal pytest warnings system, but since ``3.8`` pytest is using the builtin warning
system for its own warnings, so those two functions are now deprecated.

``Config.warn`` should be replaced by calls to the standard ``warnings.warn``, example:

.. code-block:: python

    config.warn("C1", "some warning")

Becomes:

.. code-block:: python

    warnings.warn(pytest.PytestWarning("some warning"))

``Node.warn`` now supports two signatures:

* ``node.warn(PytestWarning("some message"))``: is now the **recommended** way to call this function.
  The warning instance must be a PytestWarning or subclass.

* ``node.warn("CI", "some message")``: this code/message form is now **deprecated** and should be converted to the warning instance form above.


``pytest_namespace``
~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.7

This hook is deprecated because it greatly complicates the pytest internals regarding configuration and initialization, making some
bug fixes and refactorings impossible.

Example of usage:

.. code-block:: python

    class MySymbol:
        ...


    def pytest_namespace():
        return {"my_symbol": MySymbol()}


Plugin authors relying on this hook should instead require that users now import the plugin modules directly (with an appropriate public API).

As a stopgap measure, plugin authors may still inject their names into pytest's namespace, usually during ``pytest_configure``:

.. code-block:: python

    import pytest


    def pytest_configure():
        pytest.my_symbol = MySymbol()



Calling fixtures directly
~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.7

Calling a fixture function directly, as opposed to request them in a test function, is deprecated.

For example:

.. code-block:: python

    @pytest.fixture
    def cell():
        return ...


    @pytest.fixture
    def full_cell():
        cell = cell()
        cell.make_full()
        return cell

This is a great source of confusion to new users, which will often call the fixture functions and request them from test functions interchangeably, which breaks the fixture resolution model.

In those cases just request the function directly in the dependent fixture:

.. code-block:: python

    @pytest.fixture
    def cell():
        return ...


    @pytest.fixture
    def full_cell(cell):
        cell.make_full()
        return cell

``Node.get_marker``
~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.6

As part of a large :ref:`marker-revamp`, :meth:`_pytest.nodes.Node.get_marker` is deprecated. See
:ref:`the documentation <update marker code>` on tips on how to update your code.


record_xml_property
~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.5

The ``record_xml_property`` fixture is now deprecated in favor of the more generic ``record_property``, which
can be used by other consumers (for example ``pytest-html``) to obtain custom information about the test run.

This is just a matter of renaming the fixture as the API is the same:

.. code-block:: python

    def test_foo(record_xml_property):
        ...

Change to:

.. code-block:: python

    def test_foo(record_property):
        ...

pytest_plugins in non-top-level conftest files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.5

Defining ``pytest_plugins`` is now deprecated in non-top-level conftest.py
files because they will activate referenced plugins *globally*, which is surprising because for all other pytest
features ``conftest.py`` files are only *active* for tests at or below it.

Metafunc.addcall
~~~~~~~~~~~~~~~~

.. deprecated:: 3.3

:meth:`_pytest.python.Metafunc.addcall` was a precursor to the current parametrized mechanism. Users should use
:meth:`_pytest.python.Metafunc.parametrize` instead.

marks in ``pytest.mark.parametrize``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.2

Applying marks to values of a ``pytest.mark.parametrize`` call is now deprecated. For example:

.. code-block:: python

    @pytest.mark.parametrize(
        "a, b", [(3, 9), pytest.mark.xfail(reason="flaky")(6, 36), (10, 100)]
    )
    def test_foo(a, b):
        ...

This code applies the ``pytest.mark.xfail(reason="flaky")`` mark to the ``(6, 36)`` value of the above parametrization
call.

This was considered hard to read and understand, and also its implementation presented problems to the code preventing
further internal improvements in the marks architecture.

To update the code, use ``pytest.param``:

.. code-block:: python

    @pytest.mark.parametrize(
        "a, b",
        [(3, 9), pytest.param((6, 36), marks=pytest.mark.xfail(reason="flaky")), (10, 100)],
    )
    def test_foo(a, b):
        ...



Passing command-line string to ``pytest.main()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.0

Passing a command-line string to ``pytest.main()`` is deprecated:

.. code-block:: python

    pytest.main("-v -s")

Pass a list instead:

.. code-block:: python

    pytest.main(["-v", "-s"])


By passing a string, users expect that pytest will interpret that command-line using the shell rules they are working
on (for example ``bash`` or ``Powershell``), but this is very hard/impossible to do in a portable way.


``yield`` tests
~~~~~~~~~~~~~~~

.. deprecated:: 3.0

pytest supports ``yield``-style tests, where a test function actually ``yield`` functions and values
that are then turned into proper test methods. Example:

.. code-block:: python

    def check(x, y):
        assert x ** x == y


    def test_squared():
        yield check, 2, 4
        yield check, 3, 9

This would result into two actual test functions being generated.

This form of test function doesn't support fixtures properly, and users should switch to ``pytest.mark.parametrize``:

.. code-block:: python

    @pytest.mark.parametrize("x, y", [(2, 4), (3, 9)])
    def test_squared(x, y):
        assert x ** x == y


``pytest_funcarg__`` prefix
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.0

In very early pytest versions fixtures could be defined using the ``pytest_funcarg__`` prefix:

.. code-block:: python

    def pytest_funcarg__data():
        return SomeData()

Switch over to the ``@pytest.fixture`` decorator:

.. code-block:: python

    @pytest.fixture
    def data():
        return SomeData()

[pytest] section in setup.cfg files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.0

``[pytest]`` sections in ``setup.cfg`` files should now be named ``[tool:pytest]``
to avoid conflicts with other distutils commands.

Result log (``--result-log``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.0

The ``--resultlog`` command line option has been deprecated: it is little used
and there are more modern and better alternatives, for example `pytest-tap <https://tappy.readthedocs.io/en/latest/>`_.

Removed Features
----------------

As stated in our :ref:`backwards-compatibility` policy, deprecated features are removed only in major releases after
an appropriate period of deprecation has passed.


Reinterpretation mode (``--assert=reinterp``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Removed in version 3.0.*

Reinterpretation mode has now been removed and only plain and rewrite
mode are available, consequently the ``--assert=reinterp`` option is
no longer available.  This also means files imported from plugins or
``conftest.py`` will not benefit from improved assertions by
default, you should use ``pytest.register_assert_rewrite()`` to
explicitly turn on assertion rewriting for those files.

Removed command-line options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Removed in version 3.0.*

The following deprecated commandline options were removed:

* ``--genscript``: no longer supported;
* ``--no-assert``: use ``--assert=plain`` instead;
* ``--nomagic``: use ``--assert=plain`` instead;
* ``--report``: use ``-r`` instead;

py.test-X* entry points
~~~~~~~~~~~~~~~~~~~~~~~

*Removed in version 3.0.*

Removed all ``py.test-X*`` entry points. The versioned, suffixed entry points
were never documented and a leftover from a pre-virtualenv era. These entry
points also created broken entry points in wheels, so removing them also
removes a source of confusion for users.
