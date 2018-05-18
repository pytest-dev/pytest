Revamp the internals of the ``pytest.mark`` implementation with correct per node handling which fixes a number of
long standing bugs caused by the old design. This introduces new ``Node.iter_markers(name)`` and ``Node.get_closest_mark(name)`` APIs.
Users are **strongly encouraged** to read the `reasons for the revamp in the docs <https://docs.pytest.org/en/latest/mark.html#marker-revamp-and-iteration>`_,
or jump over to details about `updating existing code to use the new APIs <https://docs.pytest.org/en/latest/mark.html#updating-code>`_.
