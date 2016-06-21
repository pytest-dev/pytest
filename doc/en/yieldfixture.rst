.. _yieldfixture:

"yield_fixture" functions
---------------------------------------------------------------

.. deprecated:: 2.10

.. versionadded:: 2.4

.. important::
    Since pytest-2.10, fixtures using the normal ``fixture`` decorator can use a ``yield``
    statement to provide fixture values and execute teardown code, exactly like ``yield_fixture``
    in previous versions.

    Marking functions as ``yield_fixture`` is still supported, but deprecated and should not
    be used in new code.
