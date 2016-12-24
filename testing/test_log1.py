from io import StringIO
import logging

# This tests that basicConfig settings from test_log2.py don't
# interfere with those from this test
def test_log():
    log_stream = StringIO()
    logging.basicConfig(stream=log_stream, level=logging.INFO)
    log = logging.getLogger()

    log.warn('test')
    assert log_stream.getvalue() == 'WARNING:root:test\n'
