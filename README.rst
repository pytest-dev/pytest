pytest-warnings
===============

py.test plugin to list Python warnings in pytest report


Usage
-----

install via::

    pip install pytest-warnings

if you then type::

    py.test -rw

any warnings in your code are reported in the pytest report.
You can use the ``-W`` option or ``--pythonwarnings`` exactly like for the ``python`` executable.

The following example ignores all warnings, but prints DeprecationWarnings once per occurrence::

    py.test -rw -W ignore -W once::DeprecationWarning

You can also turn warnings into actual errors::

    py.test -W error


Changes
=======

0.1.0 - 2016-06-27
------------------

- Initial release.
  [fschulze (Florian Schulze)]
