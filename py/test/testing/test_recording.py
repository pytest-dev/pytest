import py,sys
py.test.skip("implementation missing: recording")

from py.__.test.testing import suptest
from py.__.test.acceptance_test import AcceptBase

class TestRecordingAccept(AcceptBase):
    def test_recording_and_back(self):
        p = self.makepyfile(test_one="""
            import py
            def test_fail():
                assert x
            def test_skip():
                py.test.skip("hello")
            def test_pass():
                pass
        """)
        rdir = py.path.local("rdir")
        result = self.runpytest(p, "--record=%s" %(rdir))
        record = py.test.RecordDir(result)
        testrun = record.getlastrun()
        assert testrun.sys.platform == sys.platform 
        assert testrun.sys.version_info == sys.version_info 
        assert testrun.sys.executable == sys.executable 

        baseadress = ("test_one.py",)
        failures = testrun.getfailures()
        assert len(failures) == 1
        failure = failures[0] 
        assert failure.testaddress == baseadress + ("test_fail",)
        assert failure.location.find("test_one.py:3") != -1
        assert failure.errmessage
        assert failure.reprfailure  # probably just a string for now
         
        skipped = testrun.getskipped()
        assert len(skipped) == 1
        skip = skipped[0] 
        assert skip.testaddress == baseaddress + ("test_skip",)
        assert skip.location == "test_one.py:7"

        passed = testrun.getpassed()
        assert len(passed) == 1
        p = passed[0] 
        assert p.testaddress == baseaddress + ("test_skip",)

