import py

#
# main entry point
#

def main(args=None):
    warn_about_missing_assertion()
    if args is None:
        args = py.std.sys.argv[1:]
    config = py.test.config
    config.parse(args)
    session = config.initsession()
    try: 
        failures = session.main()
        if failures: 
            raise SystemExit, 1 
    except KeyboardInterrupt: 
        if not config.option.verbose: 
            print
            print "KeyboardInterrupt (-v to see traceback)"
            raise SystemExit, 2
        else: 
            raise 

def warn_about_missing_assertion():
    try:
        assert False
    except AssertionError:
        pass
    else:
        py.std.warnings.warn("Assertions are turned off!"
                             " (are you using python -O?)")
