
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


Customizing tracebacks
----------------------

To filter the traceback of a custom :class:`pytest.Item` while keeping pytest's
standard failure formatting, override
:meth:`~_pytest.nodes.Node.traceback_filter` instead of ``repr_failure``.
For example, an item which executes tests through a helper module can keep only
frames from its own file:

.. code-block:: python

    import pytest


    class CustomItem(pytest.Item):
        def traceback_filter(
            self, excinfo: pytest.ExceptionInfo[BaseException]
        ) -> pytest.Traceback:
            def keep(entry: pytest.TracebackEntry) -> bool:
                return entry.path == self.path

            return excinfo.traceback.filter(keep)

Adapt the predicate to your test format; the example assumes that executing the
test produces Python frames whose paths match the item's path.
The predicate returns ``True`` for frames to keep. You can also start from
``super().traceback_filter(excinfo)`` to extend the inherited filtering.
The default filtering is unchanged: the base ``Item`` returns the original
traceback, while other node classes, such as ``Function``, provide their own
filtering.

The standard formatter continues to handle pytest's special exceptions and
traceback styles (``--tb``). With ``--full-trace``, filtering is bypassed.
An item that overrides ``repr_failure`` must use the inherited implementation
for this filtering to take effect.

Existing ``_traceback_filter`` overrides continue to work. If an item overrides
both names, ``traceback_filter`` takes precedence.
