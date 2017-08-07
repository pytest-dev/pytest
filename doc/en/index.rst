.. raw:: html

    <style>
        .row {clear: both}

        .column img {border: 1px solid black;}

        @media only screen and (min-width: 1000px),
               only screen and (min-width: 500px) and (max-width: 768px){

            .column {
                padding-left: 5px;
                padding-right: 5px;
                float: left;
            }

            .column2  {
                width: 25%;
            }
        }
        h2 {border-top: 1px solid black; padding-top: 1em}
    </style>


.. _features:

pytest: helps you write better programs
=======================================

pytest is a better way to write automated tests in Python.

It makes it easy to write small tests and get started, and can scale to support complex functional
testing for very extensive applications and libraries.

It's one of the most popular Python testing libraries, and enjoys an active, supportive developer
community and an excellent ecosystem of plugins and associated tools.


Table of contents
--------------------------

.. rst-class:: clearfix row

.. rst-class:: column column2


:ref:`Tutorial <introduction>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get started with a hands-on introduction to pytest for beginners

.. rst-class:: column column2


:ref:`How-to guides <how-to>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Guides and recipes for common problems and tasks


.. rst-class:: column column2

:ref:`Reference <reference>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Technical reference - commands, modules, classes, methods


.. rst-class:: column column2

:ref:`Background <background>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Explanation and discussion of key topics and concepts


.. rst-class:: clearfix row

pytest at a glance
------------------

- Detailed info on failing :ref:`assert statements <assert>` (no need to remember ``self.assert*``
  names)
- :ref:`Auto-discovery <test discovery>` of test modules and functions
- :ref:`Modular fixtures <fixture>` for managing small or parametrized long-lived test resources
- Can run :ref:`unittest <unittest>` (including trial) and :ref:`nose <noseintegration>` test
  suites out of the box
- Rich plugin architecture, with over 150+ :ref:`external plugins <extplugins>` and thriving
  community
- Python support: 2.6,2.7,3.3,3.4,3.5, Jython, PyPy-2.3
- Platform support: Unix/Posix and Windows


Key links
^^^^^^^^^

* `pytest on PyPI <http://pypi.python.org/pypi/pytest>`_
* `pytest on GitHub <https://github.com/pytest-dev/pytest>`_
* `this documentation as PDF <https://media.readthedocs.org/pdf/pytest/latest/pytest.pdf>`_
* `this documentation as EPUB <http://media.readthedocs.org/epub/pytest/latest/pytest.epub>`_


..  toctree::
    :maxdepth: 1
    :hidden:

    introduction/index
    how-to/index
    reference/index
    background/index


About the pytest project
------------------------

..  toctree::
    :maxdepth: 2

    about/index


Usage examples
--------------

..  toctree::
    :maxdepth: 2

    example/index
