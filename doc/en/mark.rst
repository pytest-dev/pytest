
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

A new api to access markers was introduced in order to elevate the inherent design mistakes
which accumulated over the evolution of markers from simply updating the ``__dict__`` attribute of functions to something more powerful.

At the end of this evolution Markers would unintenedly pass along in class hierachies and the api for retriving them was inconsistent,
as markers from parameterization would store differently than markers from objects and markers added via ``node.add_marker``

This in turnd made it technically next to impossible to use the data of markers correctly without having a deep understanding of the broken internals.

The new api is provides :func:`_pytest.nodes.Node.iter_markers` on :py:class:`_pytest.nodes.node`  method to iterate over markers in a consistent manner.

.. warning::

	in a future major relase of pytest we will introduce class based markers,
	at which points markers will no longer be limited to instances of :py:class:`Mark`

