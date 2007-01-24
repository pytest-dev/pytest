
import os
from py.__.misc.terminal_helper import get_terminal_width

def test_terminal_width():
    """ Dummy test for get_terminal_width
    """
    assert get_terminal_width()
    try:
        def f(*args):
            raise ValueError
        import fcntl
        ioctl = fcntl.ioctl
        fcntl.ioctl = f
        cols = os.environ.get('COLUMNS', None)
        os.environ['COLUMNS'] = '42'
        assert get_terminal_width() == 41
    finally:
        fcntl.ioctl = ioctl
        if cols:
            os.environ['COLUMNS'] = cols
