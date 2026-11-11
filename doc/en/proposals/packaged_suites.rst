:orphan:

==========================
PROPOSAL: Packaged suites
==========================

.. warning::

    This document outlines a proposal for *packaged suites*: test suites that
    ship inside an installed package, declare the parameters they need, and
    are bound and run by a consuming project. Names used here are
    provisional (see `Naming`_).

Problem
-------

Libraries that define an interface often ship a conformance test suite that
every implementation must pass. Today each of them invents its own way to let
an implementation run those tests:

* pandas extension arrays: subclass ``pandas.tests.extension.base.*Tests``
  and provide the fixtures listed in a conftest file,
* fsspec: subclass ``AbstractFixtures`` and the ``Abstract*Tests`` classes
  and override ``fs`` / ``fs_path``,
* SQLAlchemy dialects: star-import ``sqlalchemy.testing.suite`` into a test
  module, star-import its pytest plugin into ``conftest.py``, and configure
  ``[sqla_testing]`` / ``[db]`` sections in ``setup.cfg``,
* array-api-tests: run the suite's own checkout with an environment variable
  naming the library under test.

All of them copy or import the tests into the consumer's tree, because pytest
has no way to collect a suite from an installed package and hand it
configuration. The consequences:

* the contract (what the consumer must provide) is documented only in prose
  or in a conftest file, and a missing input surfaces per test as
  ``fixture 'x' not found``,
* subclass-based opt-in means new tests added to the suite are silently not
  run until each consumer adds the new base class,
* a suite cannot ship a placeholder fixture with a helpful error, because a
  fixture in the suite's own conftest is more specific than the consumer's
  and wins,
* running the same suite twice with different configuration (for example
  two backends) needs ad-hoc parametrization tricks,
* node IDs of tests collected from site-packages drop the package path
  (``test_basic.py::test_x``), so two installed suites are indistinguishable.

Proposed solution
-----------------

A suite is declared in Python, in the package that ships it, and bound by the
consuming project in Python, through a hook implemented in an initial conftest
or plugin.

Declaring a suite
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # storagelib/tests/conformance/__init__.py
    import pytest

    suite = pytest.SuiteSpec(
        package=__name__,
        doc="Conformance tests for storagelib backends.",
        params={
            "backend": pytest.SuiteParam(
                "A fresh MutableMapping implementation under test (per test)."
            ),
            "url": pytest.SuiteParam(
                "Connection URL handed to the backend.", default="memory://"
            ),
        },
    )

The tests in the package are ordinary pytest tests. They receive parameters
by requesting fixtures of the same name:

.. code-block:: python

    # storagelib/tests/conformance/test_basic.py
    def test_roundtrip(backend):
        backend["k"] = 1
        assert backend["k"] == 1

Binding a suite
~~~~~~~~~~~~~~~

.. code-block:: python

    # conftest.py of the consuming project (rootdir)
    import pytest
    from storagelib.tests.conformance import suite as storage_suite


    @pytest.fixture(params=[DictBackend, DiskBackend], ids=["dict", "disk"])
    def backend_impl(request, tmp_path):
        yield request.param(tmp_path)


    def pytest_bind_suites(config):
        return [
            storage_suite.bind(id="mem", backend=backend_impl),
            storage_suite.bind(id="sqlite", backend=backend_impl, url="sqlite://"),
        ]

A bound value is either:

* a plain object, which becomes a constant fixture, or
* a fixture function, which keeps its scope, ``params``, teardown and its own
  fixture requests.

Semantics
---------

* ``bind()`` validates the values against the declared parameters
  immediately. Unknown or missing parameters raise ``UsageError`` before
  collection starts, listing every declared parameter with its doc and
  default.
* The hook is called once, before collection, and only implementations in
  initial conftests and plugins are honoured. The set of suites therefore
  never depends on collection order.
* Each bound suite becomes a collector directly below the session, named
  ``<package>[<id>]``. Its test modules get node IDs below it, for example
  ``storagelib.tests.conformance[sqlite]/test_basic.py::test_roundtrip[dict]``.
* Bound values are registered as fixtures visible only below that collector.
  They are more specific than any conftest fixture of the same name, so
  bindings never leak into other tests and a consumer's global fixture never
  leaks into the suite.
* ``conftest.py`` files inside the suite package are loaded, scoped to the
  suite collector, so suites can have internal helper fixtures.
* Selection works as usual: ``-k``, ``-m``, and node IDs. Command-line
  argument resolution learns the ``<package>[<id>]/<path>::<name>`` form.
* Modules are imported once and shared between bindings. Suites must keep
  per-binding state in fixtures, not in module globals.
* The suite's package is imported through the normal import system. This
  proposal is independent of :doc:`import_roots` (proposed alongside it):
  it is meant to work with or without configured roots and with every
  ``--import-mode``; the prototype only exercised the default ``prepend``.
  With roots configured, a suite's package belongs to an ``installed`` root.

Prototype results
-----------------

A prototype plugin (about 100 lines, against pytest main) confirmed:

* two bindings of one suite plus the project's own tests collect and run
  with the node IDs above, and each binding sees its own values,
* a parametrized fixture as a bound value multiplies the suite as expected,
* ``-k "sqlite and url"`` selects within a binding,
* a misspelt parameter fails at startup with the full parameter listing,
* a global fixture with the same name as a parameter does not override the
  binding.

It also showed what core must add: loading suite-internal conftests,
suite-aware node-ID arguments, and public replacements for the private
fixture-registration APIs the prototype used.

Relation to ensembles
---------------------

The experimental ``_pytest.ensemble`` work (#14809) assembles a small pytest
from parts handed to it programmatically. A bound suite is a natural
*source* for an ensemble: a suite author could test their own declaration
hermetically with ``run_tests(suite.bind(id="t", backend=dict))``.
The two features should share vocabulary where they meet and stay distinct
where they don't: ensembles are about how pytest runs, packaged suites are
about what gets collected.

Naming
------

Constraints found while prototyping:

* any class name matching ``python_classes`` (default ``Test*``) is picked
  up by collection when imported into a test module. A ``TestSuite``
  declaration class triggers ``PytestCollectionWarning: cannot collect test
  class 'TestSuite' because it has a __init__ constructor``, so ``Test*``
  names are ruled out,
* ``unittest.TestSuite`` already exists and is supported by pytest,
* "testsuite" already means the junit-xml ``<testsuite>`` element
  (``junit_suite_name``, ``record_testsuite_property``),
* the ensemble work uses ``*Spec`` for frozen declarative data
  (``ConfigSpec``) and "source" for things handed in to be collected.

Provisional choice: ``pytest.SuiteSpec``, ``pytest.SuiteParam``,
``SuiteSpec.bind()`` returning a ``BoundSuite``, and the hook
``pytest_bind_suites(config)``.

Open questions
--------------

* final names (see `Naming`_),
* whether suites may declare required plugins or ini options, and how those
  are scoped to the suite collector,
* whether suites should be discoverable (for example
  ``pytest --suites`` listing installed declarations through an entry
  point), or only ever bound explicitly,
* whether parameters need types or validators beyond ``doc`` and
  ``default``.

Test cases
----------

* a declared suite bound once and twice collects with distinct node IDs,
* missing and unknown parameters fail before collection with the parameter
  listing,
* plain values and fixture functions both bind, including parametrized and
  yield fixtures,
* a consumer fixture with a parameter's name does not reach the suite, and
  bound values do not reach the consumer's own tests,
* suite-internal conftest fixtures are visible inside the suite only,
* hook implementations in non-initial conftests are rejected with a clear
  error,
* node-ID arguments in the ``<package>[<id>]/...`` form select tests.
