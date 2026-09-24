
.. _`non-python tests`:

Working with non-python tests
====================================================

.. _`yaml plugin`:

A basic example for specifying tests in Yaml files
--------------------------------------------------------------

.. _`pytest-yamlwsgi`: https://pypi.org/project/pytest-yamlwsgi/

Here is an example ``conftest.py`` (extracted from Ali Afshar's special purpose `pytest-yamlwsgi`_ plugin).   This ``conftest.py`` will  collect ``test*.yaml`` files and will execute the yaml-formatted content as custom tests:

.. include:: nonpython/conftest.py
    :literal:

You can create a simple example file:

.. include:: nonpython/test_simple.yaml
    :literal:

and if you installed :pypi:`PyYAML` or a compatible YAML-parser you can
now execute the test specification:

.. code-block:: pytest

    nonpython $ pytest test_simple.yaml
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project/nonpython
    collected 2 items

    test_simple.yaml F.                                                  [100%]

    ================================= FAILURES =================================
    ______________________________ usecase: hello ______________________________
    usecase execution failed
       spec failed: 'some': 'other'
       no further details known at this point.
    ========================= short test summary info ==========================
    FAILED test_simple.yaml::hello - usecase execution failed
    ======================= 1 failed, 1 passed in 0.12s ========================

.. regendoc:wipe

You get one dot for the passing ``sub1: sub1`` check and one failure.
Obviously in the above ``conftest.py`` you'll want to implement a more
interesting interpretation of the yaml-values.  You can easily write
your own domain-specific testing language this way.

.. note::

    ``repr_failure(excinfo)`` is called for representing test failures.
    If you create custom collection nodes you can return an error
    representation string of your choice.  It
    will be reported as a (red) string.

``reportinfo()`` is used for representing the test location and is also
consulted when reporting in ``verbose`` mode. It should return a tuple
``(path, lineno, description)``, where:

* ``path`` is the path shown in reports (usually ``self.path`` or ``self.fspath``).
* ``lineno`` is the line number, or ``0`` when no specific line applies.
* ``description`` is a short label shown for the collected item:

.. code-block:: pytest

    nonpython $ pytest -v
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y -- $PYTHON_PREFIX/bin/python
    cachedir: .pytest_cache
    rootdir: /home/sweet/project/nonpython
    collecting ... collected 2 items

    test_simple.yaml::hello FAILED                                       [ 50%]
    test_simple.yaml::ok PASSED                                          [100%]

    ================================= FAILURES =================================
    ______________________________ usecase: hello ______________________________
    usecase execution failed
       spec failed: 'some': 'other'
       no further details known at this point.
    ========================= short test summary info ==========================
    FAILED test_simple.yaml::hello - usecase execution failed
    ======================= 1 failed, 1 passed in 0.12s ========================

.. regendoc:wipe

While developing your custom test collection and execution it's also
interesting to look at the collection tree:

.. code-block:: pytest

    nonpython $ pytest --collect-only
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project/nonpython
    collected 2 items

    <Package nonpython>
      <YamlFile test_simple.yaml>
        <YamlItem hello>
        <YamlItem ok>

    ======================== 2 tests collected in 0.12s ========================

.. _`non-python parametrization`:

Letting non-python tests take part in parametrization
-----------------------------------------------------

.. versionadded:: 9.2

A collector which yields items directly, as ``YamlFile`` above does, produces a
fixed set of tests. To let a test *definition* be parametrized -- by
:hook:`pytest_generate_tests`, exactly like a Python test function -- collect
:class:`~_pytest.nodes.ItemDefinition` nodes instead of items.

Such a node declares the names it accepts in
:attr:`~_pytest.nodes.ItemDefinition.parametrize_argnames` and builds one item
per parameter set in :meth:`~_pytest.nodes.ItemDefinition.make_item`. The values
chosen for a given item arrive on ``item.callspec.params``:

.. code-block:: python

    # content of conftest.py
    from _pytest import nodes
    import pytest


    class YamlItem(pytest.Item):
        def __init__(self, *, spec, **kwargs):
            super().__init__(**kwargs)
            self.spec = spec

        def runtest(self): ...

        def reportinfo(self):
            return self.path, 0, self.name


    class YamlDefinition(nodes.ItemDefinition):
        parametrize_argnames = ("value",)

        def make_item(self, parent, *, name, callspec, nodeid, context):
            params = dict(callspec.params) if callspec is not None else {}
            return YamlItem.from_parent(parent, name=name, nodeid=nodeid, spec=params)

Any ``pytest_generate_tests`` implementation now applies:

.. code-block:: python

    def pytest_generate_tests(metafunc):
        if "value" in metafunc.fixturenames:
            metafunc.parametrize("value", ["good", "bad"])

which collects ``test_simple.yaml::hello[good]`` and
``test_simple.yaml::hello[bad]`` under a single ``<YamlDefinition hello>`` node.
Parameter ids, ``pytest.param(...)`` marks and node-id selection all work as
they do for Python tests.

.. note::

    This path covers parametrization only: there is no fixture resolution for
    non-Python items, so ``indirect=True`` and requesting fixtures from such an
    item are not supported. A ``parametrize()`` call naming anything outside
    ``parametrize_argnames`` is rejected at collection time.
