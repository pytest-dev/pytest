
import py
failure_demo = py.magic.autopath().dirpath('failure_demo.py')

pytest_plugins = "pytest_pytester"

def test_failure_demo_fails_properly(testdir): 
    sorter = testdir.inline_run(failure_demo)
    passed, skipped, failed = sorter.countoutcomes() 
    assert passed == 0 
    assert failed == 20, failed
    colreports = sorter.getnamed("collectionreport")
    failed = len([x.failed for x in colreports])
    assert failed == 5
