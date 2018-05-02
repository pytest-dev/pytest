Revamp the internals of the ``pytest.mark`` implementation with correct per node handling and introduce a new ``Node.iter_markers``
API for mark iteration over nodes which fixes a number of long standing bugs caused by the old approach. More details can be
found in `the marks documentation <https://docs.pytest.org/en/latest/mark.html#marker-revamp-and-iteration>`_.
