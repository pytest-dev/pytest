'''some classes to handle text reports'''

import sys
import py
from py.__.test.terminal import out
from py.__.test.terminal.terminal import TerminalSession

class Null:
    """ Null objects always and reliably "do nothing." """

    def __init__(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): return self
    def __repr__(self): return "Null()"
    def __str__(self): return repr(self) + ' with id:' + str(id(self))
    def __nonzero__(self): return 0

    def __getattr__(self, name): return self
    def __setattr__(self, name, value): return self
    def __delattr__(self, name): return self

    
_NotExecuted = 'NotExecuted'
_Passed = 'Passed'
_Failed = 'Failed'
_Skipped = 'Skipped'
_ExceptionFailure = 'ExceptionFailure'

class Status(object):
    '''Represents  py.test.Collector.Outcome as a string.
    Possible values: NotExecuted, Passed, Skipped, Failed, ExceptionFailure'''

    def NotExecuted(cls):
        return cls('NotExecuted')
    NotExecuted = classmethod(NotExecuted) 

    def Passed(cls):
        return cls('Passed')
    Passed = classmethod(Passed) 

    def Failed(cls):
        return cls('Failed')
    Failed = classmethod(Failed) 

    def Skipped(cls):
        return cls('Skipped')
    Skipped = classmethod(Skipped) 

    def ExceptionFailure(cls):
        return cls(_ExceptionFailure)
    ExceptionFailure = classmethod(ExceptionFailure) 

    ordered_list = [_NotExecuted,
                    _Passed,
                    _Skipped,
                    _Failed,
                    _ExceptionFailure]
        
    namemap = {
        py.test.Item.Passed: _Passed,
        py.test.Item.Skipped: _Skipped,
        py.test.Item.Failed: _Failed,
        }
    
    def __init__(self, outcome_or_name = ''):
        self.str = _NotExecuted
        if isinstance(outcome_or_name, py.test.Item.Outcome):
            for restype, name in self.namemap.items():
                if isinstance(outcome_or_name, restype):
                    self.str = name
        else:
            if str(outcome_or_name) in self.ordered_list:
                self.str = str(outcome_or_name)

    def __repr__(self):
        return 'Status("%s")' % self.str

    def __str__(self):
        return self.str

    def update(self, status):
        '''merge self and status, self will be set to the "higher" status
        in ordered_list'''
        name_int_map = dict(zip(self.ordered_list, range(len(self.ordered_list))))
        self.str = self.ordered_list[max([name_int_map[i]
                                          for i in (str(status), self.str)])]
        
    def __eq__(self, other):
        return self.str == other.str

    def __ne__(self, other):
        return not self.__eq__(other)

class OutBuffer(out.Out):
    '''Simple MockObject for py.__.test.report.text.out.Out.
    Used to get the output of TerminalSession.'''
    def __init__(self, fullwidth = 80 -1):
        self.output = []
        self.fullwidth = fullwidth

    def line(self, s= ''):
        self.output.append(str(s) + '\n')

    def write(self, s):
        self.output.append(str(s))

    def getoutput(self):
        return ''.join(self.output)

    def rewrite(self, s=''):
        self.write(s)

   


class TestReport(object):
    '''"Channel-save" report of a py.test.Collector.Outcome instance'''   

    root_id = 'TestReport Root ID'
    template = {'time' : 0,
                'label': 'Root',
                'id': root_id,
                'full_id': tuple(),
                'status': Status.NotExecuted(),
                'report': 'NoReport',
                'error_report': '',
                'finished': False,
                'restart_params': None, # ('',('',))
                'path' : '',
                'modpath': '',
                'is_item': False,
                'stdout': '',
                'stderr': '',
                }
    Status = Status
    
    def fromChannel(cls, kwdict):
        ''' TestReport.fromChannel(report.toChannel()) == report '''
        if 'status' in kwdict:
            kwdict['status'] = Status(kwdict['status'])
        return cls(**kwdict)
    fromChannel = classmethod(fromChannel)

    def __init__(self, **kwargs):
        # copy status -> deepcopy
        kwdict = py.std.copy.deepcopy(self.template)
        kwdict.update(kwargs)
        for key, value in kwdict.iteritems():
            setattr(self, key, value)

    def start(self, collector):
        '''Session.start should call this to init the report'''
        self.full_id = tuple(collector.listnames())
        self.id = collector.name
        if collector.getpathlineno(): # save for Null() in test_util.py
            fspath, lineno = collector.getpathlineno()
            if lineno != sys.maxint:
                str_append = ' [%s:%s]' % (fspath.basename, lineno)
            else:
                str_append = ' [%s]' % fspath.basename
            self.label = collector.name + str_append
            
        self.path = '/'.join(collector.listnames())
        #self.modpath = collector.getmodpath()
        self.settime()
        self.restart_params = (str(collector.listchain()[0].fspath),
                               collector.listnames())
        self.status = Status.NotExecuted()
        self.is_item = isinstance(collector, py.test.Item)

    def finish(self, collector, res, config = Null()):
        '''Session.finish should call this to set the
        value of error_report
        option is passed to Session at initialization'''
        self.settime()
        if collector.getpathlineno(): # save for Null() in test_util.py
            fspath, lineno = collector.getpathlineno()
            if lineno != sys.maxint:
                str_append = ' [%s:%s] %0.2fsecs' % (fspath.basename,
                                                     lineno, self.time)
            else:
                str_append = ' [%s] %0.2fsecs' % (fspath.basename, self.time)
            self.label = collector.name + str_append
        if res:
            if Status(res) == Status.Failed():
                self.error_report = self.report_failed(config, collector, res)
            elif Status(res) ==  Status.Skipped():
                self.error_report = self.report_skipped(config, collector, res)
            self.status.update(Status(res))
        out, err = collector.getouterr()
        self.stdout, self.stderr = str(out), str(err)
        self.finished = True

    def abbrev_path(self, fspath):
        parts = fspath.parts() 
        basename = parts.pop().basename
        while parts and parts[-1].basename in ('testing', 'test'): 
            parts.pop() 
        base = parts[-1].basename
        if len(base) < 13: 
            base = base + "_" * (13-len(base))
        return base + "_" + basename 

    def report_failed(self, config, item, res):
        #XXX hack abuse of TerminalSession
        terminal = TerminalSession(config)
        out = OutBuffer()
        terminal.out = out
        terminal.repr_failure(item, res)
        #terminal.repr_out_err(item)
        return out.getoutput()

    def report_skipped(self, config, item, outcome):
        texts = {}
        terminal = TerminalSession(config)
        raisingtb = terminal.getlastvisible(outcome.excinfo.traceback) 
        fn = raisingtb.frame.code.path
        lineno = raisingtb.lineno
        d = texts.setdefault(outcome.excinfo.exconly(), {})
        d[(fn, lineno)] = outcome
        out = OutBuffer()
        out.sep('_', 'reasons for skipped tests')
        for text, dict in texts.items():
            for (fn, lineno), outcome in dict.items(): 
                out.line('Skipped in %s:%d' %(fn, lineno))
            out.line("reason: %s" % text) 

        return out.getoutput()
        
    def settime(self):
        '''update self.time '''
        self.time = py.std.time.time() - self.time 

    def to_channel(self):
        '''counterpart of classmethod fromChannel'''
        ret = self.template.copy()
        for key in ret.keys():
            ret[key] = getattr(self, key, self.template[key])
        ret['status'] = str(ret['status'])
        return ret

    def __str__(self):
        return str(self.to_channel())

    def __repr__(self):
        return str(self)

    def copy(self, **kwargs):
        channel_dict = self.to_channel()
        channel_dict.update(kwargs)
        return TestReport.fromChannel(channel_dict)


class TestFileWatcher:
    '''watches files or paths'''
    def __init__(self, *paths):
        self.paths = [py.path.local(path) for path in paths]
        self.watchdict = dict()

    def file_information(self, path):
        try:
            return path.stat().st_ctime
        except:
            return None

    def check_files(self):
        '''returns (changed files, deleted files)'''
        def fil(p):
            return p.check(fnmatch='[!.]*.py')
        def rec(p):
            return p.check(dotfile=0)
        files = []
        for path in self.paths:
            if path.check(file=1):
                files.append(path)
            else:
                files.extend(path.visit(fil, rec))
        newdict = dict(zip(files, [self.file_information(p) for p in files]))
        files_deleted = [f for f in self.watchdict.keys()
                         if not newdict.has_key(f)]
        files_new = [f for f in newdict.keys() if not self.watchdict.has_key(f)]
        files_changed = [f for f in newdict.keys() if self.watchdict.has_key(f)
                         and newdict[f]!= self.watchdict[f]]
        files_changed = files_new + files_changed

        self.watchdict = newdict
        return files_changed, files_deleted

    def changed(self):
        '''returns False if nothing changed'''
        changed, deleted = self.check_files()
        return changed != [] or deleted != []
