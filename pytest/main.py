__all__ = []
import py, pytest

def main(args=None):
    import sys
    if args is None:
        args = sys.argv[1:]
    config = py.test.config
    config.parse(args)
    try:
        exitstatus = config.hook.pytest_cmdline_main(config=config)
    except config.Error:
        e = sys.exc_info()[1]
        sys.stderr.write("ERROR: %s\n" %(e.args[0],))
        exitstatus = 3
    py.test.config = config.__class__()
    return exitstatus

