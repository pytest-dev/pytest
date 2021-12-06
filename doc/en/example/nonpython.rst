
.. _`non-python tests`:

Working with non-python tests
====================================================

.. _`yaml plugin`:

A basic example for specifying tests in Yaml files
--------------------------------------------------------------

.. _`pytest-yamlwsgi`: http://bitbucket.org/aafshar/pytest-yamlwsgi/src/tip/pytest_yamlwsgi.py

Here is an example ``conftest.py`` (extracted from Ali Afshar's special purpose `pytest-yamlwsgi`_ plugin).   This ``conftest.py`` will  collect ``test*.yaml`` files and will execute the yaml-formatted content as custom tests:

.. include:: nonpython/conftest.py
    :literal:

You can create a simple example file:

.. include:: nonpython/test_simple.yaml
    :literal:

and if you installed :pypi:`PyYAML` or a compatible YAML-parser you can
now execute the test specification:

.. code-block:: pytest

    nonpython $ pytest test_simple.yaml
    Traceback (most recent call last):
      File "$PYTHON_PREFIX/bin/pytest", line 8, in <module>
        sys.exit(console_main())
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 188, in console_main
        code = main()
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 146, in main
        config = _prepareconfig(args, plugins)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 325, in _prepareconfig
        config = pluginmanager.hook.pytest_cmdline_parse(
      File "$PYTHON_SITE/pluggy/_hooks.py", line 265, in __call__
        return self._hookexec(self.name, self.get_hookimpls(), kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_manager.py", line 80, in _hookexec
        return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_callers.py", line 55, in _multicall
        gen.send(outcome)
      File "$PYTHON_SITE/_pytest/helpconfig.py", line 102, in pytest_cmdline_parse
        config: Config = outcome.get_result()
      File "$PYTHON_SITE/pluggy/_result.py", line 60, in get_result
        raise ex[1].with_traceback(ex[2])
      File "$PYTHON_SITE/pluggy/_callers.py", line 39, in _multicall
        res = hook_impl.function(*args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1002, in pytest_cmdline_parse
        self.parse(args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1290, in parse
        self._preparse(args, addopts=addopts)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1192, in _preparse
        self.hook.pytest_load_initial_conftests(
      File "$PYTHON_SITE/pluggy/_hooks.py", line 265, in __call__
        return self._hookexec(self.name, self.get_hookimpls(), kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_manager.py", line 80, in _hookexec
        return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_callers.py", line 60, in _multicall
        return outcome.get_result()
      File "$PYTHON_SITE/pluggy/_result.py", line 60, in get_result
        raise ex[1].with_traceback(ex[2])
      File "$PYTHON_SITE/pluggy/_callers.py", line 39, in _multicall
        res = hook_impl.function(*args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1069, in pytest_load_initial_conftests
        self.pluginmanager._set_initial_conftests(
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 512, in _set_initial_conftests
        self._try_load_conftest(anchor, namespace.importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 520, in _try_load_conftest
        self._getconftestmodules(anchor, importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 554, in _getconftestmodules
        mod = self._importconftest(conftestpath, importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 609, in _importconftest
        self.consider_conftest(mod)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 690, in consider_conftest
        self.register(conftestmodule, name=conftestmodule.__file__)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 446, in register
        ret: Optional[str] = super().register(plugin, name)
      File "$PYTHON_SITE/pluggy/_manager.py", line 114, in register
        self._verify_hook(hook, hookimpl)
      File "$PYTHON_SITE/pluggy/_manager.py", line 232, in _verify_hook
        raise PluginValidationError(
    pluggy._manager.PluginValidationError: Plugin '/home/sweet/project/nonpython/conftest.py' for hook 'pytest_collect_file'
    hookimpl definition: pytest_collect_file(parent, fspath)
    Argument(s) {'fspath'} are declared in the hookimpl but can not be found in the hookspec

.. regendoc:wipe

You get one dot for the passing ``sub1: sub1`` check and one failure.
Obviously in the above ``conftest.py`` you'll want to implement a more
interesting interpretation of the yaml-values.  You can easily write
your own domain specific testing language this way.

.. note::

    ``repr_failure(excinfo)`` is called for representing test failures.
    If you create custom collection nodes you can return an error
    representation string of your choice.  It
    will be reported as a (red) string.

``reportinfo()`` is used for representing the test location and is also
consulted when reporting in ``verbose`` mode:

.. code-block:: pytest

    nonpython $ pytest -v
    Traceback (most recent call last):
      File "$PYTHON_PREFIX/bin/pytest", line 8, in <module>
        sys.exit(console_main())
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 188, in console_main
        code = main()
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 146, in main
        config = _prepareconfig(args, plugins)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 325, in _prepareconfig
        config = pluginmanager.hook.pytest_cmdline_parse(
      File "$PYTHON_SITE/pluggy/_hooks.py", line 265, in __call__
        return self._hookexec(self.name, self.get_hookimpls(), kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_manager.py", line 80, in _hookexec
        return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_callers.py", line 55, in _multicall
        gen.send(outcome)
      File "$PYTHON_SITE/_pytest/helpconfig.py", line 102, in pytest_cmdline_parse
        config: Config = outcome.get_result()
      File "$PYTHON_SITE/pluggy/_result.py", line 60, in get_result
        raise ex[1].with_traceback(ex[2])
      File "$PYTHON_SITE/pluggy/_callers.py", line 39, in _multicall
        res = hook_impl.function(*args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1002, in pytest_cmdline_parse
        self.parse(args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1290, in parse
        self._preparse(args, addopts=addopts)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1192, in _preparse
        self.hook.pytest_load_initial_conftests(
      File "$PYTHON_SITE/pluggy/_hooks.py", line 265, in __call__
        return self._hookexec(self.name, self.get_hookimpls(), kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_manager.py", line 80, in _hookexec
        return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_callers.py", line 60, in _multicall
        return outcome.get_result()
      File "$PYTHON_SITE/pluggy/_result.py", line 60, in get_result
        raise ex[1].with_traceback(ex[2])
      File "$PYTHON_SITE/pluggy/_callers.py", line 39, in _multicall
        res = hook_impl.function(*args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1069, in pytest_load_initial_conftests
        self.pluginmanager._set_initial_conftests(
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 515, in _set_initial_conftests
        self._try_load_conftest(current, namespace.importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 520, in _try_load_conftest
        self._getconftestmodules(anchor, importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 554, in _getconftestmodules
        mod = self._importconftest(conftestpath, importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 609, in _importconftest
        self.consider_conftest(mod)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 690, in consider_conftest
        self.register(conftestmodule, name=conftestmodule.__file__)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 446, in register
        ret: Optional[str] = super().register(plugin, name)
      File "$PYTHON_SITE/pluggy/_manager.py", line 114, in register
        self._verify_hook(hook, hookimpl)
      File "$PYTHON_SITE/pluggy/_manager.py", line 232, in _verify_hook
        raise PluginValidationError(
    pluggy._manager.PluginValidationError: Plugin '/home/sweet/project/nonpython/conftest.py' for hook 'pytest_collect_file'
    hookimpl definition: pytest_collect_file(parent, fspath)
    Argument(s) {'fspath'} are declared in the hookimpl but can not be found in the hookspec

.. regendoc:wipe

While developing your custom test collection and execution it's also
interesting to just look at the collection tree:

.. code-block:: pytest

    nonpython $ pytest --collect-only
    Traceback (most recent call last):
      File "$PYTHON_PREFIX/bin/pytest", line 8, in <module>
        sys.exit(console_main())
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 188, in console_main
        code = main()
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 146, in main
        config = _prepareconfig(args, plugins)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 325, in _prepareconfig
        config = pluginmanager.hook.pytest_cmdline_parse(
      File "$PYTHON_SITE/pluggy/_hooks.py", line 265, in __call__
        return self._hookexec(self.name, self.get_hookimpls(), kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_manager.py", line 80, in _hookexec
        return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_callers.py", line 55, in _multicall
        gen.send(outcome)
      File "$PYTHON_SITE/_pytest/helpconfig.py", line 102, in pytest_cmdline_parse
        config: Config = outcome.get_result()
      File "$PYTHON_SITE/pluggy/_result.py", line 60, in get_result
        raise ex[1].with_traceback(ex[2])
      File "$PYTHON_SITE/pluggy/_callers.py", line 39, in _multicall
        res = hook_impl.function(*args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1002, in pytest_cmdline_parse
        self.parse(args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1290, in parse
        self._preparse(args, addopts=addopts)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1192, in _preparse
        self.hook.pytest_load_initial_conftests(
      File "$PYTHON_SITE/pluggy/_hooks.py", line 265, in __call__
        return self._hookexec(self.name, self.get_hookimpls(), kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_manager.py", line 80, in _hookexec
        return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
      File "$PYTHON_SITE/pluggy/_callers.py", line 60, in _multicall
        return outcome.get_result()
      File "$PYTHON_SITE/pluggy/_result.py", line 60, in get_result
        raise ex[1].with_traceback(ex[2])
      File "$PYTHON_SITE/pluggy/_callers.py", line 39, in _multicall
        res = hook_impl.function(*args)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 1069, in pytest_load_initial_conftests
        self.pluginmanager._set_initial_conftests(
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 515, in _set_initial_conftests
        self._try_load_conftest(current, namespace.importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 520, in _try_load_conftest
        self._getconftestmodules(anchor, importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 554, in _getconftestmodules
        mod = self._importconftest(conftestpath, importmode, rootpath)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 609, in _importconftest
        self.consider_conftest(mod)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 690, in consider_conftest
        self.register(conftestmodule, name=conftestmodule.__file__)
      File "$PYTHON_SITE/_pytest/config/__init__.py", line 446, in register
        ret: Optional[str] = super().register(plugin, name)
      File "$PYTHON_SITE/pluggy/_manager.py", line 114, in register
        self._verify_hook(hook, hookimpl)
      File "$PYTHON_SITE/pluggy/_manager.py", line 232, in _verify_hook
        raise PluginValidationError(
    pluggy._manager.PluginValidationError: Plugin '/home/sweet/project/nonpython/conftest.py' for hook 'pytest_collect_file'
    hookimpl definition: pytest_collect_file(parent, fspath)
    Argument(s) {'fspath'} are declared in the hookimpl but can not be found in the hookspec
