import py

#
# main entry point
#

def main(args=None):
    warn_about_missing_assertion()
    if args is None:
        args = py.std.sys.argv[1:]
    config = py.test.config
    try:
        config.parse(args) 
        config.pytestplugins.do_configure(config)
        session = config.initsession()
        exitstatus = session.main()
        config.pytestplugins.do_unconfigure(config)
        raise SystemExit(exitstatus)
    except config.Error, e:
        py.std.sys.stderr.write("ERROR: %s\n" %(e.args[0],))
        raise SystemExit(3)

def warn_about_missing_assertion():
    try:
        assert False
    except AssertionError:
        pass
    else:
        py.std.warnings.warn("Assertions are turned off!"
                             " (are you using python -O?)")
