from _pytest.reports import CollectReport
from _pytest.reports import TestReport


class TestReportSerialization(object):
    """
    All the tests in this class came originally from test_remote.py in xdist (ca03269).
    """

    def test_xdist_longrepr_to_str_issue_241(self, testdir):
        testdir.makepyfile(
            """
            import os
            def test_a(): assert False
            def test_b(): pass
        """
        )
        reprec = testdir.inline_run()
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 6
        test_a_call = reports[1]
        assert test_a_call.when == "call"
        assert test_a_call.outcome == "failed"
        assert test_a_call._to_json()["longrepr"]["reprtraceback"]["style"] == "long"
        test_b_call = reports[4]
        assert test_b_call.when == "call"
        assert test_b_call.outcome == "passed"
        assert test_b_call._to_json()["longrepr"] is None

    def test_xdist_report_longrepr_reprcrash_130(self, testdir):
        reprec = testdir.inline_runsource(
            """
                    import py
                    def test_fail(): assert False, 'Expected Message'
                """
        )
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 3
        rep = reports[1]
        added_section = ("Failure Metadata", str("metadata metadata"), "*")
        rep.longrepr.sections.append(added_section)
        d = rep._to_json()
        a = TestReport._from_json(d)
        # Check assembled == rep
        assert a.__dict__.keys() == rep.__dict__.keys()
        for key in rep.__dict__.keys():
            if key != "longrepr":
                assert getattr(a, key) == getattr(rep, key)
        assert rep.longrepr.reprcrash.lineno == a.longrepr.reprcrash.lineno
        assert rep.longrepr.reprcrash.message == a.longrepr.reprcrash.message
        assert rep.longrepr.reprcrash.path == a.longrepr.reprcrash.path
        assert rep.longrepr.reprtraceback.entrysep == a.longrepr.reprtraceback.entrysep
        assert (
            rep.longrepr.reprtraceback.extraline == a.longrepr.reprtraceback.extraline
        )
        assert rep.longrepr.reprtraceback.style == a.longrepr.reprtraceback.style
        assert rep.longrepr.sections == a.longrepr.sections
        # Missing section attribute PR171
        assert added_section in a.longrepr.sections

    def test_reprentries_serialization_170(self, testdir):
        from _pytest._code.code import ReprEntry

        reprec = testdir.inline_runsource(
            """
                            def test_repr_entry():
                                x = 0
                                assert x
                        """,
            "--showlocals",
        )
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 3
        rep = reports[1]
        d = rep._to_json()
        a = TestReport._from_json(d)

        rep_entries = rep.longrepr.reprtraceback.reprentries
        a_entries = a.longrepr.reprtraceback.reprentries
        for i in range(len(a_entries)):
            assert isinstance(rep_entries[i], ReprEntry)
            assert rep_entries[i].lines == a_entries[i].lines
            assert rep_entries[i].reprfileloc.lineno == a_entries[i].reprfileloc.lineno
            assert (
                rep_entries[i].reprfileloc.message == a_entries[i].reprfileloc.message
            )
            assert rep_entries[i].reprfileloc.path == a_entries[i].reprfileloc.path
            assert rep_entries[i].reprfuncargs.args == a_entries[i].reprfuncargs.args
            assert rep_entries[i].reprlocals.lines == a_entries[i].reprlocals.lines
            assert rep_entries[i].style == a_entries[i].style

    def test_reprentries_serialization_196(self, testdir):
        from _pytest._code.code import ReprEntryNative

        reprec = testdir.inline_runsource(
            """
                            def test_repr_entry_native():
                                x = 0
                                assert x
                        """,
            "--tb=native",
        )
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 3
        rep = reports[1]
        d = rep._to_json()
        a = TestReport._from_json(d)

        rep_entries = rep.longrepr.reprtraceback.reprentries
        a_entries = a.longrepr.reprtraceback.reprentries
        for i in range(len(a_entries)):
            assert isinstance(rep_entries[i], ReprEntryNative)
            assert rep_entries[i].lines == a_entries[i].lines

    def test_itemreport_outcomes(self, testdir):
        reprec = testdir.inline_runsource(
            """
            import py
            def test_pass(): pass
            def test_fail(): 0/0
            @py.test.mark.skipif("True")
            def test_skip(): pass
            def test_skip_imperative():
                py.test.skip("hello")
            @py.test.mark.xfail("True")
            def test_xfail(): 0/0
            def test_xfail_imperative():
                py.test.xfail("hello")
        """
        )
        reports = reprec.getreports("pytest_runtest_logreport")
        assert len(reports) == 17  # with setup/teardown "passed" reports
        for rep in reports:
            d = rep._to_json()
            newrep = TestReport._from_json(d)
            assert newrep.passed == rep.passed
            assert newrep.failed == rep.failed
            assert newrep.skipped == rep.skipped
            if newrep.skipped and not hasattr(newrep, "wasxfail"):
                assert len(newrep.longrepr) == 3
            assert newrep.outcome == rep.outcome
            assert newrep.when == rep.when
            assert newrep.keywords == rep.keywords
            if rep.failed:
                assert newrep.longreprtext == rep.longreprtext

    def test_collectreport_passed(self, testdir):
        reprec = testdir.inline_runsource("def test_func(): pass")
        reports = reprec.getreports("pytest_collectreport")
        for rep in reports:
            d = rep._to_json()
            newrep = CollectReport._from_json(d)
            assert newrep.passed == rep.passed
            assert newrep.failed == rep.failed
            assert newrep.skipped == rep.skipped

    def test_collectreport_fail(self, testdir):
        reprec = testdir.inline_runsource("qwe abc")
        reports = reprec.getreports("pytest_collectreport")
        assert reports
        for rep in reports:
            d = rep._to_json()
            newrep = CollectReport._from_json(d)
            assert newrep.passed == rep.passed
            assert newrep.failed == rep.failed
            assert newrep.skipped == rep.skipped
            if rep.failed:
                assert newrep.longrepr == str(rep.longrepr)

    def test_extended_report_deserialization(self, testdir):
        reprec = testdir.inline_runsource("qwe abc")
        reports = reprec.getreports("pytest_collectreport")
        assert reports
        for rep in reports:
            rep.extra = True
            d = rep._to_json()
            newrep = CollectReport._from_json(d)
            assert newrep.extra
            assert newrep.passed == rep.passed
            assert newrep.failed == rep.failed
            assert newrep.skipped == rep.skipped
            if rep.failed:
                assert newrep.longrepr == str(rep.longrepr)
