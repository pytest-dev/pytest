.. _deprecations:

Deprecations and Removals
=========================

This page lists all pytest features that are currently deprecated or have been removed in previous major releases.
The objective is to give users a clear rationale why a certain feature has been removed, and what alternatives can be
used instead.

Deprecated Features
-------------------


``Config.warn`` and ``Node.warn``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 3.8

Those methods were part of the internal pytest warnings system, but since ``3.8`` pytest is using the builtin warning
system for its own warnings, so those two functions are now deprecated.

``Config.warn`` should be replaced by calls to the standard ``warnings.warn``.

``Node.warn`` now supports two signatures:

* ``node.warn(PytestWarning("some message"))``: is now the recommended way to call this function.
  The warning instance must be a PytestWarning or subclass.

* ``node.warn("CI", "some message")``: this code/message form is now deprecated and should be converted to the warning instance form above.


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
