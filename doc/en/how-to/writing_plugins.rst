.. _plugins:
.. _`writing-plugins`:

Writing plugins
===============

It is easy to implement `local conftest plugins`_ for your own project
or `pip-installable plugins`_ that can be used throughout many projects,
including third party projects.  Please refer to :ref:`using plugins` if you
only want to use but not write plugins.

A plugin contains one or multiple hook functions. :ref:`Writing hooks <writinghooks>`
explains the basics and details of how you can write a hook function yourself.
``pytest`` implements all aspects of configuration, collection, running and
reporting by calling :ref:`well specified hooks <hook-reference>` of the following plugins:

* builtin plugins: loaded from pytest's internal ``_pytest`` directory.

* :ref:`external plugins <extplugins>`: installed third-party modules discovered
  through :ref:`entry points <pip-installable plugins>` in their packaging metadata

* `conftest.py plugins`_: modules auto-discovered in test directories

In principle, each hook call is a ``1:N`` Python function call where ``N`` is the
number of registered implementation functions for a given specification.
All specifications and implementations follow the ``pytest_`` prefix
naming convention, making them easy to distinguish and find.

.. _`pluginorder`:

Plugin discovery order at tool startup
--------------------------------------

``pytest`` loads plugin modules at tool startup in the following way:

1. by scanning the command line for the ``-p no:name`` option
   and *blocking* that plugin from being loaded (even builtin plugins can
   be blocked this way). This happens before normal command-line parsing.

2. by loading all builtin plugins.

3. by scanning the command line for the ``-p name`` option
   and loading the specified plugin. This happens before normal command-line parsing.

4. by loading all plugins registered through installed third-party package
   :ref:`entry points <pip-installable plugins>`, unless the
   :envvar:`PYTEST_DISABLE_PLUGIN_AUTOLOAD` environment variable is set.

5. by loading all plugins specified through the :envvar:`PYTEST_PLUGINS` environment variable.

6. by loading all "initial" :file:`conftest.py` files:

   - determine the test paths: specified on the command line, otherwise in
     :confval:`testpaths` if defined and running from the rootdir, otherwise the
     current dir
   - for each test path, load ``conftest.py`` and ``test*/conftest.py`` relative
     to the directory part of the test path, if they exist. Before a ``conftest.py``
     file is loaded, load ``conftest.py`` files in its parent directories up to
     the :option:`--confcutdir` limit. When ``--confcutdir`` is not provided,
     the cutoff defaults to the directory containing the config file, or to the
     :ref:`rootdir <rootdir>` if no config file is found.
     After a ``conftest.py`` file is loaded, recursively load all plugins specified
     in its :globalvar:`pytest_plugins` variable if present.


.. _`conftest.py plugins`:
.. _`localplugin`:
.. _`local conftest plugins`:

conftest.py: local per-directory plugins
----------------------------------------

Local ``conftest.py`` plugins contain directory-specific hook
implementations.  Hook Session and test running activities will
invoke all hooks defined in ``conftest.py`` files closer to the
root of the filesystem.  Example of implementing the
``pytest_runtest_setup`` hook so that is called for tests in the ``a``
sub directory but not for other directories::

    a/conftest.py:
        def pytest_runtest_setup(item):
            # called for running each test in 'a' directory
            print("setting up", item)

    a/test_sub.py:
        def test_sub():
            pass

    test_flat.py:
        def test_flat():
            pass

Here is how you might run it::

     pytest test_flat.py --capture=no  # will not show "setting up"
     pytest a/test_sub.py --capture=no  # will show "setting up"

.. note::
    If you have ``conftest.py`` files which do not reside in a
    python package directory (i.e. one containing an ``__init__.py``) then
    "import conftest" can be ambiguous because there might be other
    ``conftest.py`` files as well on your ``PYTHONPATH`` or ``sys.path``.
    It is thus good practice for projects to either put ``conftest.py``
    under a package scope or to never import anything from a
    ``conftest.py`` file.

    See also: :ref:`pythonpath`.

.. note::
    Some hooks cannot be implemented in conftest.py files which are not
    :ref:`initial <pluginorder>` due to how pytest discovers plugins during
    startup. See the documentation of each hook for details.

Writing your own plugin
-----------------------

If you want to write a plugin, there are many real-life examples
you can copy from:

* a custom collection example plugin: :ref:`yaml plugin`
* builtin plugins which provide pytest's own functionality
* many :ref:`external plugins <plugin-list>` providing additional features

All of these plugins implement :ref:`hooks <hook-reference>` and/or :ref:`fixtures <fixture>`
to extend and add functionality.

.. note::
    Make sure to check out the excellent
    `cookiecutter-pytest-plugin <https://github.com/pytest-dev/cookiecutter-pytest-plugin>`_
    project, which is a `cookiecutter template <https://github.com/audreyr/cookiecutter>`_
    for authoring plugins.

    The template provides an excellent starting point with a working plugin,
    tests running with tox, a comprehensive README file as well as a
    pre-configured entry-point.

Also consider :ref:`contributing your plugin to pytest-dev<submitplugin>`
once it has some happy users other than yourself.


.. _`setuptools entry points`:
.. _`pip-installable plugins`:

Making your plugin installable by others
----------------------------------------

If you want to make your plugin externally available, you
may define a so-called entry point for your distribution so
that ``pytest`` finds your plugin module. Entry points are
a feature that is provided by :std:doc:`packaging tools
<packaging:specifications/entry-points>`.

pytest looks up the ``pytest11`` entrypoint to discover its
plugins, thus you can make your plugin available by defining
it in your ``pyproject.toml`` file.

.. sourcecode:: toml

    # sample ./pyproject.toml file
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [project]
    name = "myproject"
    classifiers = [
        "Framework :: Pytest",
    ]

    [project.entry-points.pytest11]
    myproject = "myproject.pluginmodule"

If a package is installed this way, ``pytest`` will load
``myproject.pluginmodule`` as a plugin which can define
:ref:`hooks <hook-reference>`. Confirm registration with ``pytest --trace-config``

.. note::

    Make sure to include ``Framework :: Pytest`` in your list of
    `PyPI classifiers <https://pypi.org/classifiers/>`_
    to make it easy for users to find your plugin.


.. _assertion-rewriting:

Assertion Rewriting
-------------------

One of the main features of ``pytest`` is the use of plain assert
statements and the detailed introspection of expressions upon
assertion failures.  This is provided by "assertion rewriting" which
modifies the parsed AST before it gets compiled to bytecode.  This is
done via a :pep:`302` import hook which gets installed early on when
``pytest`` starts up and will perform this rewriting when modules get
imported.  However, since we do not want to test different bytecode
from what you will run in production, this hook only rewrites test modules
themselves (as defined by the :confval:`python_files` configuration option),
and any modules which are part of plugins.
Any other imported module will not be rewritten and normal assertion behaviour
will happen.

If you have assertion helpers in other modules where you would need
assertion rewriting to be enabled you need to ask ``pytest``
explicitly to rewrite this module before it gets imported.

.. autofunction:: pytest.register_assert_rewrite
    :noindex:

This is especially important when you write a pytest plugin which is
created using a package.  The import hook only treats ``conftest.py``
files and any modules which are listed in the ``pytest11`` entrypoint
as plugins.  As an example consider the following package::

   pytest_foo/__init__.py
   pytest_foo/plugin.py
   pytest_foo/helper.py

With the following typical ``pyproject.toml`` extract:

.. code-block:: toml

   [project.entry-points.pytest11]
   foo = "pytest_foo.plugin"

In this case only ``pytest_foo/plugin.py`` will be rewritten.  If the
helper module also contains assert statements which need to be
rewritten it needs to be marked as such, before it gets imported.
This is easiest by marking it for rewriting inside the
``__init__.py`` module, which will always be imported first when a
module inside a package is imported.  This way ``plugin.py`` can still
import ``helper.py`` normally.  The contents of
``pytest_foo/__init__.py`` will then need to look like this:

.. code-block:: python

   import pytest

   pytest.register_assert_rewrite("pytest_foo.helper")


Requiring/Loading plugins in a test module or conftest file
-----------------------------------------------------------

You can require plugins in a test module or a ``conftest.py`` file using :globalvar:`pytest_plugins`:

.. code-block:: python

    pytest_plugins = ["name1", "name2"]

When the test module or conftest plugin is loaded the specified plugins
will be loaded as well. Any module can be blessed as a plugin, including internal
application modules:

.. code-block:: python

    pytest_plugins = "myapp.testsupport.myplugin"

The entry point name of an installed plugin can also be used, just like with
the :option:`-p` command-line option:

.. code-block:: python

    pytest_plugins = ("xdist",)

:globalvar:`pytest_plugins` are processed recursively, so note that in the example above
if ``myapp.testsupport.myplugin`` also declares :globalvar:`pytest_plugins`, the contents
of the variable will also be loaded as plugins, and so on.

.. _`requiring plugins in non-root conftests`:

.. note::
    Requiring plugins using :globalvar:`pytest_plugins` variable in non-root
    ``conftest.py`` files is deprecated.

    This is important because ``conftest.py`` files implement per-directory
    hook implementations, but once a plugin is imported, it will affect the
    entire directory tree. In order to avoid confusion, defining
    :globalvar:`pytest_plugins` in any ``conftest.py`` file which is not located in the
    tests root directory is deprecated, and will raise a warning.

This mechanism makes it easy to share fixtures within applications or even
external applications without the need to create external plugins using the
:std:doc:`entry point packaging metadata
<packaging:guides/creating-and-discovering-plugins>` technique.

Plugins imported by :globalvar:`pytest_plugins` will also automatically be marked
for assertion rewriting (see :func:`pytest.register_assert_rewrite`).
However for this to have any effect the module must not be
imported already; if it was already imported at the time the
:globalvar:`pytest_plugins` statement is processed, a warning will result and
assertions inside the plugin will not be rewritten.  To fix this you
can either call :func:`pytest.register_assert_rewrite` yourself before
the module is imported, or you can arrange the code to delay the
importing until after the plugin is registered.


Accessing another plugin by name
--------------------------------

If a plugin wants to collaborate with code from
another plugin it can obtain a reference through
the plugin manager like this:

.. sourcecode:: python

    plugin = config.pluginmanager.get_plugin("name_of_plugin")

If you want to look at the names of existing plugins, use
the :option:`--trace-config` option.


.. _declaring-config-options:

Declaring configuration options
-------------------------------

.. versionadded:: 9.2

.. note::

    :func:`parser.addconfig() <pytest.Parser.addconfig>` and the ``fallback``
    argument to :func:`parser.addini() <pytest.Parser.addini>` are
    experimental. Their behaviour and signatures may change in future
    releases.

A setting that your plugin reads -- a name to greet, a format to print in, a
limit to enforce -- is declared once, from the :hook:`pytest_addoption` hook,
with :func:`parser.addconfig() <pytest.Parser.addconfig>`:

.. code-block:: python

    def pytest_addoption(parser):
        parser.addconfig(
            "hello_name",
            'Name to greet, as in "Hello World!"',
            type=str,
            default="World",
            cli="--hello-name",
            metavar="NAME",
            group="helloworld",
        )

This gives users both a ``hello_name`` configuration option and a
``--hello-name`` command line option. There is one way to read it, whichever
way the user set it:

.. code-block:: python

    @pytest.fixture
    def hello(request):
        def _hello(name=None):
            return f"Hello {name or request.config.getini('hello_name')}!"

        return _hello

The command line option *overrides* the configuration option rather than being
a separate value, which is what lets there be a single read. Leave ``cli`` out
and the setting is configuration-only; users can still change it for one run
with ``-o hello_name=Bob``, so a setting does not need a command line option
merely to be overridable.

Types
~~~~~

``type`` accepts ``str``, ``bool``, ``int`` and ``float``, a union of those
such as ``int | str``, a ``Literal`` of strings for a fixed set of choices, and
the list-valued tags ``"args"``, ``"linelist"`` and ``"paths"``:

.. code-block:: python

    from typing import Literal

    parser.addconfig(
        "hello_style",
        "How enthusiastic to be",
        type=Literal["plain", "shouting"],
        default="plain",
        cli="--hello-style",
    )

Declaring the type once is what makes ``-o hello_style=whispering`` a clean
usage error: it is enforced wherever the value comes from -- a configuration
file, ``-o``, or the command line option.

A ``bool`` setting becomes a flag taking no argument. Pass ``cli_value`` to
make a flag out of any other type, so that a ``--shout`` flag can set
``hello_style`` to ``shouting``.

Falling back to another setting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When one setting refines another -- a format for one output stream, defaulting
to the format used for all of them -- say so with ``fallback`` rather than
resolving it at each place you read the value:

.. code-block:: python

    parser.addconfig("hello_name", "Name to greet", type=str, default="World")
    parser.addconfig(
        "hello_shout_name",
        "Name to greet when shouting",
        type=str,
        default="World",
        fallback="hello_name",
    )

``config.getini("hello_shout_name")`` then returns ``hello_name`` whenever
``hello_shout_name`` itself is not configured. A fallback must be registered
before the settings naming it, and must have the same type; several may be
given, and the first one that is configured wins.

Declaring the fallback also gets two things right that are easy to miss when
writing the chain by hand: a setting explicitly configured to an empty value is
honoured rather than falling through, and ``pytest --help`` says what this
setting falls back to.

Reading a setting
~~~~~~~~~~~~~~~~~

:func:`config.getini() <pytest.Config.getini>` reads a setting whichever way
the user set it. :class:`config.settings <pytest.Settings>` is the same values
as a mapping, and can also say where one came from:

.. code-block:: python

    config.settings["hello_name"]  # same as config.getini("hello_name")
    config.settings.source_of("hello_name")  # Source.FILE, Source.CLI, ...
    config.settings.spec("hello_name").default  # how it was declared

Note that a setting is *not* read as ``config.option.<name>``. That still
works, and shows the resolved value, but it is deprecated: writing it there
does not change the setting. ``config.option`` remains the way to read the
command line options that are not settings, which are also listed as
``config.settings.options``.

The underlying calls
~~~~~~~~~~~~~~~~~~~~

``addconfig`` is a convenience over two lower-level calls, which remain
available and are what you want when a setting is not really a setting:

* :func:`parser.addoption() <pytest.Parser.addoption>` registers a command line
  option only, taking argparse's arguments and read with
  :func:`config.getoption() <pytest.Config.getoption>`. Use it for things that
  are not configuration at all -- selecting what to run, entering a debugger,
  anything meaningless to write down in a file.
* :func:`parser.addini() <pytest.Parser.addini>` registers a configuration
  option only, read with :func:`config.getini() <pytest.Config.getini>`. It
  also accepts ``fallback``.

Note that their ``type`` arguments are unrelated: ``addoption`` takes an
argparse converter, ``addini`` takes the types described above.


.. _registering-markers:

Registering custom markers
--------------------------

If your plugin uses any markers, you should register them so that they appear in
pytest's help text and do not :ref:`cause spurious warnings <unknown-marks>`.
For example, the following plugin would register ``cool_marker`` and
``mark_with`` for all users:

.. code-block:: python

    def pytest_configure(config):
        config.addinivalue_line("markers", "cool_marker: this one is for cool tests.")
        config.addinivalue_line(
            "markers", "mark_with(arg, arg2): this marker takes arguments."
        )


Testing plugins
---------------

pytest comes with a plugin named ``pytester`` that helps you write tests for
your plugin code. The plugin is disabled by default, so you will have to enable
it before you can use it.

You can do so by adding the following line to a ``conftest.py`` file in your
testing directory:

.. code-block:: python

    # content of conftest.py

    pytest_plugins = ["pytester"]

Alternatively you can invoke pytest with the ``-p pytester`` command line
option.

This will allow you to use the :py:class:`pytester <pytest.Pytester>`
fixture for testing your plugin code.

Let's demonstrate what you can do with the plugin with an example. Imagine we
developed a plugin that provides a fixture ``hello`` which yields a function
and we can invoke this function with one optional parameter. It will return a
string value of ``Hello World!`` if we do not supply a value or ``Hello
{value}!`` if we do supply a string value.

.. code-block:: python

    import pytest


    def pytest_addoption(parser):
        parser.addconfig(
            "hello_name",
            'Default "name" for hello().',
            type=str,
            default="World",
            cli="--hello-name",
            metavar="NAME",
            group="helloworld",
        )


    @pytest.fixture
    def hello(request):
        def _hello(name=None):
            if not name:
                name = request.config.getini("hello_name")
            return f"Hello {name}!"

        return _hello


Now the ``pytester`` fixture provides a convenient API for creating temporary
``conftest.py`` files and test files. It also allows us to run the tests and
return a result object, with which we can assert the tests' outcomes.

.. code-block:: python

    def test_hello(pytester):
        """Make sure that our plugin works."""

        # create a temporary conftest.py file
        pytester.makeconftest(
            """
            import pytest

            @pytest.fixture(params=[
                "Brianna",
                "Andreas",
                "Floris",
            ])
            def name(request):
                return request.param
        """
        )

        # create a temporary pytest test file
        pytester.makepyfile(
            """
            def test_hello_default(hello):
                assert hello() == "Hello World!"

            def test_hello_name(hello, name):
                assert hello(name) == "Hello {0}!".format(name)
        """
        )

        # run all tests with pytest
        result = pytester.runpytest()

        # check that all 4 tests passed
        result.assert_outcomes(passed=4)

.. note::

    :meth:`pytest.RunResult.assert_outcomes` parses pytest's standard terminal
    summary. A plugin that changes or removes that summary can make outcome
    parsing fail. Disable the output-changing plugin for the nested run with
    ``-p no:<plugin>``, or set ``PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`` when the
    nested run should not discover third-party plugins.


Additionally it is possible to copy examples to the ``pytester``'s isolated environment
before running pytest on it. This way we can abstract the tested logic to separate files,
which is especially useful for longer tests and/or longer ``conftest.py`` files.

Note that for ``pytester.copy_example`` to work we need to set `pytester_example_dir`
in our configuration file to tell pytest where to look for example files.

.. code-block:: toml

    # content of pytest.toml
    [pytest]
    pytester_example_dir = "."


.. code-block:: python

    # content of test_example.py


    def test_plugin(pytester):
        pytester.copy_example("test_example.py")
        pytester.runpytest("-k", "test_example")


    def test_example():
        pass

.. code-block:: pytest

    $ pytest
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project
    configfile: pytest.toml
    collected 2 items

    test_example.py ..                                                   [100%]

    ============================ 2 passed in 0.12s =============================

For more information about the result object that ``runpytest()`` returns, and
the methods that it provides please check out the :py:class:`RunResult
<_pytest.pytester.RunResult>` documentation.
