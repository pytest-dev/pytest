import py

#
# main entry point
#

def main(args=None):
    warn_about_missing_assertion()
    if args is None:
        args = py.std.sys.argv[1:]
    elif isinstance(args, basestring):
        args = args.split(" ")
    config = py.test.config
    config.parse(args)
    sessionclass = config.getsessionclass() 
    
    # ok, some option checks
    if config.option.startserver or config.option.runbrowser:
        from py.__.test.rsession.rsession import AbstractSession, LSession
        if not issubclass(sessionclass, AbstractSession):
            print "Cannot use web server without (R|L)Session, using lsession"
            sessionclass = LSession
    if config.option.apigen:
        from py.__.test.rsession.rsession import AbstractSession, LSession
        if not issubclass(sessionclass, AbstractSession):
            sessionclass = LSession
            print "Cannot generate API without (R|L)Session, using lsession"
    if config.option.restreport:
        from py.__.test.rsession.rsession import AbstractSession, LSession
        if not issubclass(sessionclass, AbstractSession):
            sessionclass = LSession
    
    session = sessionclass(config)
    
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
