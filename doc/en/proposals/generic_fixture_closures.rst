:orphan:

============================================
PROPOSAL: Generic fixture closures for items
============================================

.. warning::

    This document is the follow-up half of the ``ItemDefinition`` work: it
    outlines what is needed for *non-Python* items to request fixtures. The
    parametrization half has shipped, see :ref:`non-python parametrization`.

What shipped
------------

:class:`~_pytest.nodes.ItemDefinition` lets any collector take part in
:hook:`pytest_generate_tests`. A definition declares the names it accepts up
front:

.. code-block:: python

    class YamlDefinition(nodes.ItemDefinition):
        parametrize_argnames = ("value",)

        def make_item(self, parent, *, name, callspec, nodeid, context):
            return YamlItem.from_parent(
                parent, name=name, nodeid=nodeid, spec=dict(callspec.params)
            )

and the values chosen for each parameter set arrive on ``item.callspec.params``.

``ParametrizeContext`` deliberately has no fixture machinery: ``_infer_scope()``
returns ``Scope.Function``, ``_register_direct_params()`` is a no-op, and
``_validate_argnames()`` checks against ``parametrize_argnames`` rather than a
fixture closure. ``FixtureManager.pytest_generate_tests`` returns early for a
context which is not a ``Metafunc``.

That covers parametrization. It does **not** cover:

- ``indirect=True`` -- there is no fixture to hand ``request.param`` to.
- scope inference from fixture scopes -- an unspecified ``scope=`` is always
  function scope.
- a non-Python item requesting a fixture at all, including one at the new
  ``"definition"`` scope.

Why the rest is not a small step
--------------------------------

Fixture resolution is written against ``Function``, not against ``Item``. The
concrete couplings:

**TopRequest assumes a Python function item.**
It is constructed as ``TopRequest(pyfuncitem=item)`` and reads
``item._fixtureinfo``, ``item.funcargs``, ``item.fixturenames`` and
``item.obj``. ``_fillfixtures()`` writes into ``item.funcargs``.
``request.instance`` walks to a :class:`~pytest.Class` node and calls
``newinstance()``.

**getfixtureinfo() is item-scoped and signature-driven.**
Its closure starts from the function's argument names
(``getfuncargnames(func)``) plus autouse names. A non-Python definition has no
signature; its "argnames" are whatever it declares. ``FunctionDefinition``
already has to ``cast(nodes.Item, self)`` to call it -- the same wart, one level
up.

**Direct parametrization desugars into DirectParamFixtureDef.**
That is how a direct param reaches the test at setup time. Without a fixture
system there is nothing to desugar into, which is why the generic path delivers
params on the callspec instead.

**Function.setup() drives everything.**
``nodes.Item.setup()`` is a no-op; the fixture lifecycle only runs because
``Function.setup()`` calls ``self._request._fillfixtures()``.

Proposed shape
--------------

Three steps, each independently useful.

1. Split a node-level closure entry point out of ``getfixtureinfo()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Today ``getfixtureinfo(node, func, cls, ignore_args)`` derives ``initialnames``
from ``func``'s signature. Proposed:

.. code-block:: python

    def getfixtureinfo_for_argnames(
        self, node: nodes.Node, argnames: Sequence[str], *, ignore_args=()
    ) -> FuncFixtureInfo: ...

with the current signature-based version becoming a thin wrapper which computes
``argnames`` from the function. This removes the ``cast(nodes.Item, self)`` in
``FunctionDefinition`` as a side effect, and gives ``ItemDefinition`` a closure
without inventing a fake function.

2. Make the request object item-generic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Introduce a small protocol for what ``TopRequest`` needs from its item --
``fixturenames``, somewhere to store the computed values, ``_fixtureinfo``, and
an optional ``instance`` -- and give :class:`~pytest.Item` a default
implementation. :class:`~pytest.Function` keeps its current behaviour
(``funcargs``, bound instance); a generic item gets a plain dict and
``instance is None``.

The open question here is ``request.instance``, whose meaning is genuinely
Python-specific. Returning ``None`` for non-Python items is the honest answer,
but fixtures in the wild do use ``request.instance`` unconditionally.

3. Opt in per definition
~~~~~~~~~~~~~~~~~~~~~~~~

Fixture support should not be forced on every ``ItemDefinition``; a collector
which only wants parametrization should not pay for closure computation.
Suggested switch:

.. code-block:: python

    class ItemDefinition(Collector, abc.ABC):
        #: Whether items generated from this definition can request fixtures.
        supports_fixtures: bool = False

With ``supports_fixtures = True``, ``make_parametrize_context()`` computes a
closure from ``parametrize_argnames`` via step 1 and returns a fixture-aware
context, so ``indirect=True``, scope inference and ``"definition"`` scoped
fixtures all work uniformly. ``FixtureManager.pytest_generate_tests`` would then
key off the context being fixture-aware rather than off
``isinstance(metafunc, Metafunc)``.

Open questions
--------------

- Does ``Metafunc`` stay a distinct class once the generic context is
  fixture-aware, or does it collapse into ``ParametrizeContext`` plus the
  ``module``/``cls``/``function`` attributes?
- ``request.instance`` for non-Python items: ``None``, or an error on access?
- Autouse fixtures currently apply to every item in a subtree. Should they apply
  to non-Python items which opted into fixtures, or only to those which declare
  the corresponding names?
- Should ``parametrize_argnames`` and the fixture closure be the same list, or
  should a definition be able to accept a name for parametrization which is not
  requestable as a fixture?
