'''Backend for running tests and creating a Repository of testreports.'''
import py
import repository
import util
import threading

Null = util.Null

class TestRepository(repository.Repository):
    '''stores only TestReport'''
    ReportClass = util.TestReport
    failed_id = [repr(ReportClass.Status.Failed())]
    skipped_id = [repr(ReportClass.Status.Skipped())]    

    def __init__(self):
        super(TestRepository, self).__init__()
        self.add([], self.ReportClass())
        failedreport = self.ReportClass()
        failedreport.full_id = self.failed_id
        failedreport.label = 'Failed Tests'
        self.add(self.failed_id, failedreport)
        skippedreport = self.ReportClass()
        skippedreport.full_id = self.skipped_id
        skippedreport.label = 'Skipped Tests'
        self.add(self.skipped_id, skippedreport)

    def root_status(self):
        root_status = self.ReportClass.Status.NotExecuted()
        if len(self.keys()) > 2:
            root_status = self.ReportClass.Status.Passed()
        if len(self.find_children(self.skipped_id)):
            root_status = self.ReportClass.Status.Skipped()
        if len(self.find_children(self.failed_id)):
            root_status = self.ReportClass.Status.Failed()
        return root_status

    def delete_all(self, key):
        super(TestRepository, self).delete_all(key)
        new_repos = TestRepository()
        for new_key in new_repos.keys():
            if not self.haskey(new_key):
                self.add(new_key, new_repos.find(new_key))

    def delete(self, key):
        super(TestRepository, self).delete(key)
        new_repos = TestRepository()
        if new_repos.haskey(key):
            self.add(key, new_repos.find(key))

    def add_report(self, report):
        if not report.full_id:
            self.add([], report)
            return
        if report.error_report:
            if report.status == self.ReportClass.Status.Failed():
                self.add(self.failed_id + [report.id], report)
            elif report.status == self.ReportClass.Status.Skipped():
                self.add(self.skipped_id + [report.id], report)
        self.add(report.full_id, report)

    def add_report_from_channel(self, report_str):
        report = self.ReportClass.fromChannel(report_str)
        self.add_report(report)
        return report.full_id[:]


class ReportStore:
    ReportClass = util.TestReport

    def __init__(self):
        self._reports = repository.OrderedDict()
        self._repository = TestRepository()
        self.root = self.ReportClass()
        #self.add(self.ReportClass())

    def add(self, report):
        if not self._check_root(report):
            #print '/'.join(report.full_id)
            self._reports[report.full_id] = report
        self._repository.add_report(report)
        
    def _check_root(self, report):
        if report.id == self.ReportClass.root_id:
            self.root = report
            return True
        else:
            self.root.status.update(report.status)
        return False

    def add_report_from_channel(self, report_str):
        report = self.ReportClass.fromChannel(report_str)
        self.add(report)
        return report.full_id[:]
    
    def get(self, **kwargs):
        # ensure failed > skipped > passed_item
        filter_dict = repository.OrderedDict()
        filter_dict['failed'] = self._select_failed
        filter_dict['skipped']= self._select_skipped
        filter_dict['passed_item']= self._select_passed_item
        filter_dict['id']= self._select_by_id
        
        if kwargs.get('id', None) == tuple():
            return [self.root]

        selected_reports = []
        functions = [filter_dict[name] for name in kwargs.keys()
                     if filter_dict.has_key(name)]
        for function in functions:
            selected_reports.extend([rep for rep in self._reports.values()
                                     if function(rep, **kwargs)])
        return selected_reports

    def _select_failed(self, report, **kwargs):
        if kwargs['failed']:
            return report.status == self.ReportClass.Status.Failed() and report.error_report != ''
        return False
    
    def _select_skipped(self, report, **kwargs):
        if kwargs['skipped']:
            return report.status == self.ReportClass.Status.Skipped()
        return False
    
    def _select_passed_item(self, report, **kwargs):
        if kwargs['passed_item']:
            return report.status == self.ReportClass.Status.Passed() and report.is_item == True
        return False
    
    def _select_by_id(self, report, **kwargs):
        id = kwargs['id']
        return report.full_id == id

class ReportBackend:

    def __init__(self, config = Null()):
        self.reportstore = ReportStore()
        self.channel = Null()
        self.waitfinish_thread = Null()
        self.queue = py.std.Queue.Queue()
        self._message_callback = Null()
        self._messages_callback = Null()
        self.config = config

    def running(self):
        '''are there tests running?'''
        if self.channel:
            return not self.channel.isclosed()
        return False
    running = property(running)

    def shutdown(self):
        if self.running:
            self.channel.close()
        if self.waitfinish_thread.isAlive():
            self.waitfinish_thread.join()

    def get_store(self):
        return self.reportstore

    def set_message_callback(self, callback = Null()):
        self._message_callback = callback

    def set_messages_callback(self, callback = Null()):
        self._messages_callback = callback

    def update(self):
        """Check if there is something new in the queue."""
        changed_report_ids = []
        while not self.queue.empty():
            try:
                report_str = self.queue.get(False)
                id = report_str
                if report_str is not None:
                    id = self.reportstore.add_report_from_channel(report_str)
                changed_report_ids.append(id)
                self._message_callback(id)
            except py.std.Queue.Empty:
                pass
        self._messages_callback(changed_report_ids)

    def debug_queue_put(self, item):
        report = ReportStore.ReportClass.fromChannel(item)
        print '/'.join(report.full_id)
        self.queue.put(item)
        
    def start_tests(self, config = None, args = [], tests = []):
        py.test.skip("XXX fix this or remove --tkinter")
        if self.running:
            return
        if config is None:
            config = self.config
        self.testrepository = TestRepository()
        self.reportstore = ReportStore()
        self.gateway = py.execnet.PopenGateway(config.option.executable) 
        #self.channel = self.gateway.newchannel(receiver = self.queue.put)
        self.channel = self.gateway.remote_exec(source = '''
        import py
        from py.__.test.tkinter.backend import remote

        args, tests = channel.receive()
        remote(channel, tests = tests, args = args)
        # why?
        channel.close()
        ''')
        self.channel.setcallback(self.queue.put)
        self.channel.send((args, tests))
        self.waitfinish_thread = threading.Thread(target = waitfinish, args = (self.channel,))
        self.waitfinish_thread.start()

def waitfinish(channel):
    try:
        while 1:
            try:
                channel.waitclose(0.5)
            except (IOError, py.error.Error):
                continue
            break
    finally:
        try:
            channel.gateway.exit()
        except EOFError:
            # the gateway receiver callback will get woken up
            # and see an EOFError exception
            pass
            
            
                
def remote(channel, tests = [], args = []):
    import py
    from py.__.test.tkinter.reportsession import ReportSession
    from py.__.test.terminal.remote import getfailureitems
    
    config = py.test.config._reparse(args)
    if tests: 
        cols = getfailureitems(tests)
    else:
        cols = config.args 
    session = ReportSession(config = config, channel=channel) 
    session.shouldclose = channel.isclosed
    session.main()
    
