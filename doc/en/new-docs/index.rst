Pytest Documentation
====================

What is pytest?
---------------

Pytest is a mature testing framework for Python that is developed by a thriving
and ever-growing community of volunteers. It uses plain assert statements and
regular Python comparisons. Writing tests with pytest requires little to no
boilerplate code and powerful features allow easy parametrization and
intelligent test selection.

It can be easily extended and has hundreds of plugins available. Distributed
under the terms of the `MIT`_ license, pytest is free and open source software.

.. _`MIT`: https://github.com/pytest-dev/pytest/blob/master/LICENSE

.. _`installation`:

Installation
------------

**pytest** is available for download from `PyPI`_ via `pip`_::

    $ pip install -U pytest

.. _`PyPI`: https://pypi.python.org/pypi
.. _`pip`: https://pypi.python.org/pypi/pip/

To check your installation has installed the correct version::

    $ py.test --version

If you get an error checkout :ref:`installation issues`.

Audiences
---------


User
~~~~

This section covers the basics to get you running and writing automated tests
in pytest.

:ref:`user`


Advanced User
~~~~~~~~~~~~~

This section dives deeper into pytest features such as fixtures and
parametrization, how to extend pytest through hooks and gives advice on
different styles of testing.

:ref:`advanceduser`


Plugin Author
~~~~~~~~~~~~~

This section guides you in creating plugins to customize and extend pytest.

:ref:`pluginauthor`


Contributor
~~~~~~~~~~~

If you are interested in contributing to pytest, this section will point you in
the right direction.

:ref:`contributor`



References
----------

* :ref:`Command-line options <refcommandline>`
* :ref:`pytest.* namespace <refnamespace>`
* :ref:`Hooks <refhooks>`
* :ref:`Built-in fixtures <reffixtures>`
* :ref:`Magic variables <refvariables>`
