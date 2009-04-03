import py

class EventlogPlugin:
    """ log pytest events to a file. """
    def pytest_addoption(self, parser):
        parser.addoption("--eventlog", dest="eventlog", 
            help="write all pytest events to the given file.")

    def pytest_configure(self, config):
        eventlog = config.getvalue("eventlog")
        if eventlog:
            self.eventlogfile = open(eventlog, 'w')

    def pytest_unconfigure(self, config):
        if hasattr(self, 'eventlogfile'):
            self.eventlogfile.close()
            del self.eventlogfile

    def pyevent(self, eventname, args, kwargs):
        if hasattr(self, 'eventlogfile'):
            f = self.eventlogfile
            print >>f, eventname, args, kwargs
            f.flush()

# ===============================================================================
# plugin tests 
# ===============================================================================

def test_generic(plugintester):
    plugintester.apicheck(EventlogPlugin)

    testdir = plugintester.testdir()
    testdir.makepyfile("""
        def test_pass():
            pass
    """)
    testdir.runpytest("--eventlog=event.log")
    s = testdir.tmpdir.join("event.log").read()
    assert s.find("testrunstart") != -1
    assert s.find("ItemTestReport") != -1
    assert s.find("testrunfinish") != -1
