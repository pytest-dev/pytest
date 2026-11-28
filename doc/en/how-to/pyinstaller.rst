.. _freezing-pyinstaller:

How to run tests in a PyInstaller application
=============================================

If you distribute your application frozen with
`PyInstaller <https://pyinstaller.readthedocs.io>`_, you can ship your tests
with it and run them through the frozen executable. This tests the code your
users actually run, and catches modules that PyInstaller failed to include.
See also :ref:`freezing-pytest`.

PyInstaller stores the Python modules of the application in an archive
(``PYZ``) inside the executable. pytest collects tests from files on disk, so
it cannot collect test modules that only exist in that archive; this also
applies to :option:`--pyargs`, which resolves module names to file system paths
before collecting. The test files must therefore be included as data files,
while the application code stays in the archive.

Example project
---------------

Consider this layout:

.. code-block:: text

    app_main.py
    myapp.spec
    myapp/
        __init__.py
        core.py
    myapp_tests/
        __init__.py
        conftest.py
        pytest.ini
        test_core.py

The tests live in their own top-level package instead of a ``tests``
sub-package of ``myapp``. Inside the frozen application ``myapp/__init__.py``
only exists in the archive, so pytest would treat a copied ``myapp/tests``
directory as a separate top-level package named ``tests``, and modules imported
both as ``myapp.tests.helpers`` and relative to the test would be imported twice.

The application and its tests:

.. code-block:: python

    # content of myapp/core.py
    def add(a, b):
        return a + b

.. code-block:: python

    # content of myapp_tests/conftest.py
    import pytest


    @pytest.fixture
    def two():
        return 2

.. code-block:: python

    # content of myapp_tests/test_core.py
    from myapp.core import add


    def test_add(two):
        assert add(1, 1) == two


    def test_add_wrong():
        assert add(1, 1) == 3

.. code-block:: ini

    # content of myapp_tests/pytest.ini
    [pytest]
    addopts = -p no:cacheprovider

The :ref:`cache plugin <cache>` is disabled because the bundle directory may be
read-only, and in ``onefile`` mode it is removed when the program exits.

The entry point runs the tests when started with ``--pytest``, and passes any
further arguments on to pytest:

.. code-block:: python

    # content of app_main.py
    import os
    import sys


    def run_tests(args):
        import pytest

        # Inside the frozen app, sys._MEIPASS is the bundle directory
        # (``_internal`` in onedir mode, a temporary directory in onefile mode).
        # When run from source, fall back to the directory of this file.
        bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        config = os.path.join(bundle_dir, "myapp_tests", "pytest.ini")
        return pytest.main(["-c", config, "--pyargs", "myapp_tests", *args])


    if __name__ == "__main__":
        if len(sys.argv) > 1 and sys.argv[1] == "--pytest":
            sys.exit(run_tests(sys.argv[2:]))

        from myapp.core import add

        print(add(2, 3))

``-c`` points pytest at the configuration file inside the bundle. Without it,
pytest would search for a configuration file starting from the current
directory, and use whatever ``pytest.ini`` or ``pyproject.toml`` happens to be
there (see :ref:`rootdir`).

Third-party plugins are not loaded automatically in a frozen program; pass them
to ``pytest.main`` as shown in :ref:`freezing-pytest`.

The spec file
-------------

Create the spec file with ``pyi-makespec``:

.. code-block:: bash

    pyi-makespec --name myapp --add-data "myapp_tests:myapp_tests" app_main.py

which generates:

.. code-block:: python

    # content of myapp.spec
    a = Analysis(
        ["app_main.py"],
        pathex=[],
        binaries=[],
        data=[("myapp_tests", "myapp_tests")],
        hiddenimports=[],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
        optimize=0,
    )
    pyz = PYZ(a.pure)

    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="myapp",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.data,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="myapp",
    )

Each ``data`` entry is a ``(source, destination)`` pair, here copying the
``myapp_tests`` directory into the bundle. pytest itself is included by
PyInstaller's hook for pytest, because ``app_main.py`` imports it.

.. note::

    Do not add the test modules to ``hiddenimports``. If they are also in the
    archive, Python imports them from there instead of from the copied files,
    and :ref:`assertion rewriting <assert-details>` does not happen.

Building and running
--------------------

Build the application and run the tests:

.. code-block:: pytest

    $ pyinstaller myapp.spec
    $ dist/myapp/myapp --pytest
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-9.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project/dist/myapp/_internal/myapp_tests
    configfile: pytest.ini
    collected 2 items

    dist/myapp/_internal/myapp_tests/test_core.py .F                     [100%]

    ================================= FAILURES =================================
    ______________________________ test_add_wrong ______________________________

        def test_add_wrong():
    >       assert add(1, 1) == 3
    E       assert 2 == 3
    E        +  where 2 = add(1, 1)

    myapp_tests/test_core.py:9: AssertionError
    ========================= short test summary info ==========================
    FAILED dist/myapp/_internal/myapp_tests/test_core.py::test_add_wrong - assert...
    ======================= 1 failed, 1 passed in 0.12s ========================

On Windows, run ``dist\myapp\myapp.exe --pytest`` instead. The same tests also
run without freezing, using ``python app_main.py --pytest``.
