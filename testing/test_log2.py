import logging

# This tests that basicConfig settings from test_log1.py don't
# interfere with those from this test
logging.basicConfig()
log = logging.getLogger()
def test_foo():
    foo = 1
    log.warn(foo)
    assert foo == 1
