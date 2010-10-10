"""
extensible functional and unit testing with Python.
(c) Holger Krekel and others, 2004-2010
"""
__version__ = "2.0.0dev0"
import pytest.config
from pytest import collect

class cmdline: # compatibility py.test.cmdline.main == pytest.cmdline.main
    @staticmethod
    def main(args=None):
        import sys
        if args is None:
            args = sys.argv[1:]
        config = pytest.config.Config()
        config.parse(args)
        try:
            exitstatus = config.hook.pytest_cmdline_main(config=config)
        except config.Error:
            e = sys.exc_info()[1]
            sys.stderr.write("ERROR: %s\n" %(e.args[0],))
            exitstatus = EXIT_INTERNALERROR
        return exitstatus

def __main__():
    raise SystemExit(cmdline.main())
