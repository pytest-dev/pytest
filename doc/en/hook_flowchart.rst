Flowchart
=========

Flowchart:

.. graphviz::

   digraph {
      "pytest_cmdline_main" -> "pytest_plugin_registered (session)";
      "pytest_plugin_registered (session)" -> "pytest_configure";
      "pytest_configure" -> "pytest_plugin_registered (all plugins)";
      "pytest_plugin_registered (all plugins)" -> "pytest_plugin_registered (all plugins)";
      "pytest_plugin_registered (all plugins)" -> "pytest_sessionstart";
      "pytest_sessionstart" -> "pytest_plugin_registered (all plugins again)";
      "pytest_plugin_registered (all plugins again)" -> "pytest_plugin_registered (all plugins again)";
      "pytest_plugin_registered (all plugins again)" -> "pytest_report_header";
      "pytest_report_header" -> "pytest_report_header";
   }
