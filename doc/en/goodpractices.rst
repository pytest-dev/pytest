.. highlightlang:: python
.. _`goodpractices`:

Good Integration Practices
=================================================


.. _`test discovery`:
.. _`Python test discovery`:

Conventions for Python test discovery
-------------------------------------------------

``pytest`` implements the following standard test discovery:

* If no arguments are specified then collection starts from :confval:`testpaths`
  (if configured) or the current directory. Alternatively, command line arguments
  can be used in any combination of directories, file names or node ids.
* recurse into directories, unless they match :confval:`norecursedirs`
* ``test_*.py`` or ``*_test.py`` files, imported by their `test package name`_.
* ``Test`` prefixed test classes (without an ``__init__`` method)
* ``test_`` prefixed test functions or methods are test items

For examples of how to customize your test discovery :doc:`example/pythoncollection`.

Within Python modules, ``pytest`` also discovers tests using the standard
:ref:`unittest.TestCase <unittest.TestCase>` subclassing technique.


Choosing a test layout / import rules
------------------------------------------

``pytest`` supports two common test layouts:

* putting tests into an extra directory outside your actual application
  code, useful if you have many functional tests or for other reasons
  want to keep tests separate from actual application code (often a good
  idea)::

    setup.py   # your setuptools Python package metadata
    mypkg/
        __init__.py
        appmodule.py
    tests/
        test_app.py
        ...


* inlining test directories into your application package, useful if you
  have direct relation between (unit-)test and application modules and
  want to distribute your tests along with your application::

    setup.py   # your setuptools Python package metadata
    mypkg/
        __init__.py
        appmodule.py
        ...
        test/
            test_app.py
            ...

Important notes relating to both schemes:

- **make sure that "mypkg" is importable**, for example by typing once::

     pip install -e .   # install package using setup.py in editable mode

- **avoid "__init__.py" files in your test directories**.
  This way your tests can run easily against an installed version
  of ``mypkg``, independently from the installed package if it contains
  the tests or not.

- With inlined tests you might put ``__init__.py`` into test
  directories and make them installable as part of your application.
  Using the ``pytest --pyargs mypkg`` invocation pytest will
  discover where mypkg is installed and collect tests from there.
  With the "external" test you can still distribute tests but they
  will not be installed or become importable.

Typically you can run tests by pointing to test directories or modules::

    pytest tests/test_app.py       # for external test dirs
    pytest mypkg/test/test_app.py  # for inlined test dirs
    pytest mypkg                   # run tests in all below test directories
    pytest                         # run all tests below current dir
    ...

Because of the above ``editable install`` mode you can change your
source code (both tests and the app) and rerun tests at will.
Once you are done with your work, you can `use tox`_ to make sure
that the package is really correct and tests pass in all
required configurations.

.. note::

    You can use Python3 namespace packages (PEP420) for your application
    but pytest will still perform `test package name`_ discovery based on the
    presence of ``__init__.py`` files.  If you use one of the
    two recommended file system layouts above but leave away the ``__init__.py``
    files from your directories it should just work on Python3.3 and above.  From
    "inlined tests", however, you will need to use absolute imports for
    getting at your application code.

.. _`test package name`:

.. note::

    If ``pytest`` finds a "a/b/test_module.py" test file while
    recursing into the filesystem it determines the import name
    as follows:

    * determine ``basedir``: this is the first "upward" (towards the root)
      directory not containing an ``__init__.py``.  If e.g. both ``a``
      and ``b`` contain an ``__init__.py`` file then the parent directory
      of ``a`` will become the ``basedir``.

    * perform ``sys.path.insert(0, basedir)`` to make the test module
      importable under the fully qualified import name.

    * ``import a.b.test_module`` where the path is determined
      by converting path separators ``/`` into "." characters.  This means
      you must follow the convention of having directory and file
      names map directly to the import names.

    The reason for this somewhat evolved importing technique is
    that in larger projects multiple test modules might import
    from each other and thus deriving a canonical import name helps
    to avoid surprises such as a test modules getting imported twice.


.. _`virtualenv`: http://pypi.python.org/pypi/virtualenv
.. _`buildout`: http://www.buildout.org/
.. _pip: http://pypi.python.org/pypi/pip

.. _`use tox`:

Tox
------

For development, we recommend to use virtualenv_ environments and pip_
for installing your application and any dependencies
as well as the ``pytest`` package itself. This ensures your code and
dependencies are isolated from the system Python installation.

If you frequently release code and want to make sure that your actual
package passes all tests you may want to look into `tox`_, the
virtualenv test automation tool and its `pytest support
<http://testrun.org/tox/latest/example/pytest.html>`_.
Tox helps you to setup virtualenv environments with pre-defined
dependencies and then executing a pre-configured test command with
options.  It will run tests against the installed package and not
against your source code checkout, helping to detect packaging
glitches.

Continuous integration services such as Jenkins_ can make use of the
``--junitxml=PATH`` option to create a JUnitXML file and generate reports (e.g.
by publishing the results in a nice format with the `Jenkins xUnit Plugin
<https://wiki.jenkins-ci.org/display/JENKINS/xUnit+Plugin>`_).


Integrating with setuptools / ``python setup.py test`` / ``pytest-runner``
--------------------------------------------------------------------------

You can integrate test runs into your setuptools based project
with the `pytest-runner <https://pypi.python.org/pypi/pytest-runner>`_ plugin.

Add this to ``setup.py`` file:

.. code-block:: python

    from setuptools import setup

    setup(
        #...,
        setup_requires=['pytest-runner', ...],
        tests_require=['pytest', ...],
        #...,
    )


And create an alias into ``setup.cfg`` file:


.. code-block:: ini

    [aliases]
    test=pytest

If you now type::

    python setup.py test

this will execute your tests using ``pytest-runner``. As this is a
standalone version of ``pytest`` no prior installation whatsoever is
required for calling the test command. You can also pass additional
arguments to pytest such as your test directory or other
options using ``--addopts``.

You can also specify other pytest-ini options in your ``setup.cfg`` file
by putting them into a ``[tool:pytest]`` section:

.. code-block:: ini

    [tool:pytest]
    addopts = --verbose
    python_files = testing/*/*.py


.. note::
    Prior to 3.0, the supported section name was ``[pytest]``. Due to how
    this may collide with some distutils commands, the recommended
    section name for ``setup.cfg`` files is now ``[tool:pytest]``.

    Note that for ``pytest.ini`` and ``tox.ini`` files the section
    name is ``[pytest]``.


Manual Integration
^^^^^^^^^^^^^^^^^^

If for some reason you don't want/can't use ``pytest-runner``, you can write
your own setuptools Test command for invoking pytest.

.. code-block:: python

    import sys

    from setuptools.command.test import test as TestCommand


    class PyTest(TestCommand):
        user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

        def initialize_options(self):
            TestCommand.initialize_options(self)
            self.pytest_args = []

        def run_tests(self):
            #import here, cause outside the eggs aren't loaded
            import pytest
            errno = pytest.main(self.pytest_args)
            sys.exit(errno)


    setup(
        #...,
        tests_require=['pytest'],
        cmdclass = {'test': PyTest},
        )

Now if you run::

    python setup.py test

this will download ``pytest`` if needed and then run your tests
as you would expect it to. You can pass a single string of arguments
using the ``--pytest-args`` or ``-a`` command-line option. For example::

    python setup.py test -a "--durations=5"

is equivalent to running ``pytest --durations=5``.


.. include:: links.inc
