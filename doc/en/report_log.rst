.. _report_log:

Report files
============

.. versionadded:: 5.3

The ``--report-log=FILE`` option writes *report logs* into a file as the test session executes.

Each line of the report log contains a self contained JSON object corresponding to a testing event,
such as a collection or a test result report. The file is guaranteed to be flushed after writing
each line, so systems can read and process events in real-time.

Each JSON object contains a special key ``$report_type``, which contains a unique identifier for
that kind of report object. For future compatibility, consumers of the file should ignore reports
they don't recognize, as well as ignore unknown properties/keys in JSON objects that they do know,
as future pytest versions might enrich the objects with more properties/keys.

.. note::
    This option is meant to the replace ``--resultlog``, which is deprecated and meant to be removed
    in a future release. If you use ``--resultlog``, please try out ``--report-log`` and
    provide feedback.

Example
-------

Consider this file:

.. code-block:: python

    # content of test_report_example.py


    def test_ok():
        assert 5 + 5 == 10


    def test_fail():
        assert 4 + 4 == 1


.. code-block:: pytest

    $ pytest test_report_example.py -q --report-log=log.json
    .F                                                                   [100%]
    ================================= FAILURES =================================
    ________________________________ test_fail _________________________________

        def test_fail():
    >       assert 4 + 4 == 1
    E       assert (4 + 4) == 1

    test_report_example.py:8: AssertionError
    ------------------- generated report log file: log.json --------------------
    1 failed, 1 passed in 0.12s

The generated ``log.json`` will contain a JSON object per line:

::

    $ cat log.json
    {"pytest_version": "5.2.3.dev90+gd1129cf96.d20191026", "$report_type": "Header"}
    {"nodeid": "", "outcome": "passed", "longrepr": null, "result": null, "sections": [], "$report_type": "CollectReport"}
    {"nodeid": "test_report_example.py", "outcome": "passed", "longrepr": null, "result": null, "sections": [], "$report_type": "CollectReport"}
    {"nodeid": "test_report_example.py::test_ok", "location": ["test_report_example.py", 2, "test_ok"], "keywords": {"report_log.rst-39": 1, "test_report_example.py": 1, "test_ok": 1}, "outcome": "passed", "longrepr": null, "when": "setup", "user_properties": [], "sections": [], "duration": 0.00021314620971679688, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_ok", "location": ["test_report_example.py", 2, "test_ok"], "keywords": {"report_log.rst-39": 1, "test_report_example.py": 1, "test_ok": 1}, "outcome": "passed", "longrepr": null, "when": "call", "user_properties": [], "sections": [], "duration": 0.00014543533325195312, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_ok", "location": ["test_report_example.py", 2, "test_ok"], "keywords": {"report_log.rst-39": 1, "test_report_example.py": 1, "test_ok": 1}, "outcome": "passed", "longrepr": null, "when": "teardown", "user_properties": [], "sections": [], "duration": 0.00016427040100097656, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_fail", "location": ["test_report_example.py", 6, "test_fail"], "keywords": {"test_fail": 1, "test_report_example.py": 1, "report_log.rst-39": 1}, "outcome": "passed", "longrepr": null, "when": "setup", "user_properties": [], "sections": [], "duration": 0.00013589859008789062, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_fail", "location": ["test_report_example.py", 6, "test_fail"], "keywords": {"test_fail": 1, "test_report_example.py": 1, "report_log.rst-39": 1}, "outcome": "failed", "longrepr": {"reprcrash": {"path": "$REGENDOC_TMPDIR/test_report_example.py", "lineno": 8, "message": "assert (4 + 4) == 1"}, "reprtraceback": {"reprentries": [{"type": "ReprEntry", "data": {"lines": ["    def test_fail():", ">       assert 4 + 4 == 1", "E       assert (4 + 4) == 1"], "reprfuncargs": {"args": []}, "reprlocals": null, "reprfileloc": {"path": "test_report_example.py", "lineno": 8, "message": "AssertionError"}, "style": "long"}}], "extraline": null, "style": "long"}, "sections": [], "chain": [[{"reprentries": [{"type": "ReprEntry", "data": {"lines": ["    def test_fail():", ">       assert 4 + 4 == 1", "E       assert (4 + 4) == 1"], "reprfuncargs": {"args": []}, "reprlocals": null, "reprfileloc": {"path": "test_report_example.py", "lineno": 8, "message": "AssertionError"}, "style": "long"}}], "extraline": null, "style": "long"}, {"path": "$REGENDOC_TMPDIR/test_report_example.py", "lineno": 8, "message": "assert (4 + 4) == 1"}, null]]}, "when": "call", "user_properties": [], "sections": [], "duration": 0.00027489662170410156, "$report_type": "TestReport"}
    {"nodeid": "test_report_example.py::test_fail", "location": ["test_report_example.py", 6, "test_fail"], "keywords": {"test_fail": 1, "test_report_example.py": 1, "report_log.rst-39": 1}, "outcome": "passed", "longrepr": null, "when": "teardown", "user_properties": [], "sections": [], "duration": 0.00016689300537109375, "$report_type": "TestReport"}
