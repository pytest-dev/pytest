Added support for `PEP-415's <https://www.python.org/dev/peps/pep-0415/>`_
``Exception.__suppress_context__``. Now if a ``raise exception from None`` is
caught by pytest, pytest will no longer chain the context in the test report.
The behavior now matches Python's traceback behavior.
