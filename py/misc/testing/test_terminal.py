
import os
import py
from py.__.misc.terminal_helper import get_terminal_width

def test_terminal_width():
    """ Dummy test for get_terminal_width
    """
    assert get_terminal_width()
    try:
        import fcntl
    except ImportError:
        py.test.skip('fcntl not supported on this platform')
    def f(*args):
        raise ValueError
    ioctl = fcntl.ioctl
    fcntl.ioctl = f
    try:
        cols = os.environ.get('COLUMNS', None)
        os.environ['COLUMNS'] = '42'
        assert get_terminal_width() == 41
    finally:
        fcntl.ioctl = ioctl
        if cols:
            os.environ['COLUMNS'] = cols
