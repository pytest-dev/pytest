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


Advance usage
=============

You can get more fine grained filtering of warnings by using the
``filterwarnings`` configuration option.

``filterwarnings`` works like the python's ``-W`` flag except it will not
escape special characters.

Example
-------

.. code::

    # pytest.ini
    [pytest]
    filterwarnings= default
                    ignore:.*is deprecated.*:Warning
                    error::DeprecationWarning:importlib.*


Changes
=======

0.2.0 - 2016-10-24
------------------

- Add ``filterwarnings`` option.
  [Carreau (Matthias Bussonnier)]


0.1.0 - 2016-06-27
------------------

- Initial release.
  [fschulze (Florian Schulze)]
