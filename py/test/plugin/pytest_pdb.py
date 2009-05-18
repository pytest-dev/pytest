from py.__.test.custompdb import post_mortem

def pytest_item_runtest_finished(item, excinfo, outerr):
    if excinfo and item.config.option.usepdb:
        tw = py.io.TerminalWriter()
        repr = excinfo.getrepr()
        repr.toterminal(tw) 
        post_mortem(excinfo._excinfo[2])
