
.. _mark:

Marking test functions with attributes
=================================================================


By using the ``pytest.mark`` helper you can easily set
metadata on your test functions. There are
some builtin markers, for example:

* :ref:`skip <skip>` - always skip a test function
* :ref:`skipif <skipif>` - skip a test function if a certain condition is met
* :ref:`xfail <xfail>` - produce an "expected failure" outcome if a certain
  condition is met
* :ref:`parametrize <parametrizemark>` to perform multiple calls
  to the same test function.

It's easy to create custom markers or to apply markers
to whole test classes or modules. See :ref:`mark examples` for examples
which also serve as documentation.

.. note::

    Marks can only be applied to tests, having no effect on
    :ref:`fixtures <fixtures>`.


.. currentmodule:: _pytest.mark.structures
.. autoclass:: Mark
	:members:


.. `marker-iteration`

Marker iteration
=================

.. versionadded:: 3.6

pytest's marker implementation traditionally worked by simply updating the ``__dict__`` attribute of functions to add markers, in a cumulative manner. As a result of the this, markers would unintendely be passed along class hierarchies in surprising ways plus the API for retriving them was inconsistent, as markers from parameterization would be stored differently than markers applied using the ``@pytest.mark`` decorator and markers added via ``node.add_marker``.

This state of things made it technically next to impossible to use data from markers correctly without having a deep understanding of the internals, leading to subtle and hard to understand bugs in more advanced usages.

Depending on how a marker got declared/changed one would get either a ``MarkerInfo`` which might contain markers from sibling classes,
``MarkDecorators`` when marks came from parameterization or from a ``node.add_marker`` call, discarding prior marks. Also ``MarkerInfo`` acts like a single mark, when it in fact repressents a merged view on multiple marks with the same name.

On top of that markers where not accessible the same way for modules, classes, and functions/methods,
in fact, markers where only accessible in functions, even if they where declared on classes/modules.

A new API to access markers has been introduced in pytest 3.6 in order to solve the problems with the initial design, providing :func:`_pytest.nodes.Node.iter_markers` method to iterate over markers in a consistent manner and reworking the internals, which solved great deal of problems with the initial design.

.. note::

	in a future major relase of pytest we will introduce class based markers,
	at which points markers will no longer be limited to instances of :py:class:`Mark`

