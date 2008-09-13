import py
from py.__.test.session import Session
from py.__.test import event

def add_filelog_option():
    py.test.config.addoptions("filelog session options "
                              "(use --session=FileLogSession)",
        py.test.config.Option('--filelog', action="store",
                              default=None, dest="filelog",
                              help="path for filelog session logging"))
                              

def generic_path(item):
    chain = item.listchain()
    gpath = [chain[0].name]
    fspath = chain[0].fspath
    fspart = False
    for node in chain[1:]:
        newfspath = node.fspath
        if newfspath == fspath:
            if fspart:
                gpath.append(':')
                fspart = False
            else:
                gpath.append('.')            
        else:
            gpath.append('/')
            fspart = True
        name = node.name
        if name[0] in '([':
            gpath.pop()
        gpath.append(name)
        fspath = newfspath
    return ''.join(gpath)

class FileLogSession(Session):

    def __init__(self, config):
        super(FileLogSession, self).__init__(config)
        self.bus.subscribe(self.log_event_to_file)
        if hasattr(config.option, 'filelog'):
            filelog = config.option.filelog
            self.logfile = open(filelog, 'w') # line buffering ?

    def write_log_entry(self, shortrepr, name, longrepr):
        print >>self.logfile, "%s %s" % (shortrepr, name)
        for line in longrepr.splitlines():
            print >>self.logfile, " %s" % line

    def log_outcome(self, ev):
        outcome = ev.outcome
        gpath = generic_path(ev.colitem)
        self.write_log_entry(outcome.shortrepr, gpath, str(outcome.longrepr))

    def log_event_to_file(self, ev):
        if isinstance(ev, event.ItemTestReport):
            self.log_outcome(ev)
        elif isinstance(ev, event.CollectionReport):
            if not ev.passed:
                self.log_outcome(ev)
        elif isinstance(ev, event.InternalException):
            path = ev.repr.reprcrash.path # fishing :(
            self.write_log_entry('!', path, str(ev.repr))
        


