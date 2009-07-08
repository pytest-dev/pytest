
import py
failure_demo = py.magic.autopath().dirpath('failure_demo.py')

pytest_plugins = "pytest_pytester"

def test_failure_demo_fails_properly(testdir): 
    reprec = testdir.inline_run(failure_demo)
    passed, skipped, failed = reprec.countoutcomes() 
    assert passed == 0 
    assert failed == 20, failed
    colreports = reprec.getreports("pytest_collectreport")
    failed = len([x.failed for x in colreports])
    assert failed == 5
