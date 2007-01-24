import py
from py.__.test.tkinter import backend

ReportBackend = backend.ReportBackend
TestRepository = backend.TestRepository
ReportStore = backend.ReportStore

datadir = py.magic.autopath().dirpath('data')
from cStringIO import StringIO 


class Test_TestRepository:
    
    def check_repository_has_failed_and_skipped_folder(self, repos):
        assert repos.find([repr(TestRepository.ReportClass.Status.Failed())])
        assert repos.find([repr(TestRepository.ReportClass.Status.Skipped())])

    def test_repository_has_failed_and_skipped_folder(self):
        repos = TestRepository()
        self.check_repository_has_failed_and_skipped_folder(repos)

    def test_repository_has_failed_and_skipped_folder_after_delete_all(self):
        repos = TestRepository()
        self.check_repository_has_failed_and_skipped_folder(repos)
        repos.delete_all([])
        self.check_repository_has_failed_and_skipped_folder(repos)

    def test_repository_has_failed_and_skipped_folder_after_delete(self):
        repos = TestRepository()
        self.check_repository_has_failed_and_skipped_folder(repos)
        repos.delete([str(TestRepository.ReportClass.Status.Failed())])
        self.check_repository_has_failed_and_skipped_folder(repos)
        repos.delete([str(TestRepository.ReportClass.Status.Failed())])
        self.check_repository_has_failed_and_skipped_folder(repos)

    def test_add_report_from_channel(self):
        full_id = ['start', 'next', 'end']
        report = TestRepository.ReportClass()
        report.full_id = full_id

        repos = TestRepository()
        id = repos.add_report_from_channel(report.to_channel())
        assert id == full_id
        assert repos.haskey(full_id)


class TestReportStore:
    
    def setup_method(self, method):
        self.store = ReportStore()

        self.report_failed = ReportStore.ReportClass()
        self.report_failed.status = ReportStore.ReportClass.Status.Failed()
        self.report_failed.full_id = ('report_failed')
        self.report_failed.id = '1'

        self.report_failed_item = self.report_failed.copy()
        self.report_failed_item.error_report = 'Error'
        self.report_failed_item.full_id = ('report_failed_item')
        self.report_failed_item.id = '1'
        
        self.report_skipped = ReportStore.ReportClass()
        self.report_skipped.status = ReportStore.ReportClass.Status.Skipped()
        self.report_skipped.full_id = ('report_skipped')
        self.report_skipped.id = '1'

        self.report_passed = ReportStore.ReportClass()
        self.report_passed.status = ReportStore.ReportClass.Status.Passed()
        self.report_passed.full_id = ('report_passed')
        self.report_passed.id = '1'
        
        self.report_passed_item = self.report_passed.copy()
        self.report_passed_item.is_item = True
        self.report_passed_item.full_id = ('report_passed_item')
        self.report_passed_item.id = '1'
        
    def fill_store(self):
        self.store.add(self.report_failed)
        self.store.add(self.report_failed_item)
        self.store.add(self.report_skipped)
        self.store.add(self.report_passed)
        self.store.add(self.report_passed_item)
        
    def test_get_failed(self):
        self.fill_store()
        print self.store._reports.keys()
        assert len(self.store.get(failed = True)) == 1
        assert self.store.get(failed = True) == [self.report_failed_item]

    def test_get_skipped(self):
        self.fill_store()
        print self.store._reports.keys()
        assert len(self.store.get(skipped = True)) == 1
        assert self.store.get(skipped = True) == [self.report_skipped]

    def test_get_passed_item(self):
        self.fill_store()
        assert len(self.store.get(passed_item = True)) == 1
        assert self.store.get(passed_item = True) == [self.report_passed_item]
        
    def test_select_failed(self):
        assert self.store._select_failed(self.report_failed,
                                         failed = True) == False
        assert self.store._select_failed(self.report_failed_item,
                                         failed = True) == True
        assert self.store._select_failed(self.report_failed_item,
                                         failed=False) == False
        assert self.store._select_failed(self.report_skipped,
                                         failed = True,
                                         skipped = True) == False

    def test_select_skipped(self):
        assert self.store._select_skipped(self.report_failed,
                                          skipped = True) == False
        assert self.store._select_skipped(self.report_skipped,
                                          skipped = False) == False
        assert self.store._select_skipped(self.report_skipped,
                                          skipped = True) == True

    def test_select_passed_item(self):
        assert self.store._select_passed_item(self.report_failed,
                                              passed_item = True) == False
        assert self.store._select_passed_item(self.report_skipped,
                                              passed_item = True,
                                              skipped = True) == False
        assert self.store._select_passed_item(self.report_passed,
                                              passed_item = True) == False
        assert self.store._select_passed_item(self.report_passed_item,
                                              passed_item = False) == False
        assert self.store._select_passed_item(self.report_passed_item,
                                              passed_item = True) == True

    def test_select_by_id(self):
        assert self.store._select_by_id(self.report_passed_item,
                                        id = ['id']) == False
        id = ['my', 'special', 'report', 'id']
        report = self.store.ReportClass()
        report.full_id = id[:]
        assert self.store._select_by_id(report, id = id) == True
        assert self.store._select_by_id(report, id = id[:-1]) == False

    def test_add_report_from_channel(self):
        full_id = ['start', 'next', 'end']
        report = ReportStore.ReportClass()
        report.full_id = full_id

        id = self.store.add_report_from_channel(report.to_channel())
        assert id == full_id
        
        
    
class TestReportBackend:

    def setup_method(self, method):
        self.backend = ReportBackend()

    def test_get_store(self):
        assert isinstance(self.backend.get_store(), ReportStore)

    def test_running_property(self):
        backend = ReportBackend()
        assert not self.backend.running

    def test_update_callback(self):
        l = []
        self.backend.set_message_callback(l.append)
        self.backend.queue.put(None)
        self.backend.update()
        assert len(l) == 1
        assert l[0] is None

    def test_processs_messeges_callback(self):
        l = []
        self.backend.set_message_callback(l.append)
        self.backend.queue.put(None)
        self.backend.update()
        assert len(l) == 1
        assert l[0] is None

    def test_start_tests(self):
        config = py.test.config._reparse([datadir/'filetest.py'])
        self.backend.start_tests(config = config,
                                 args = config.args,
                                 tests = [])
        while self.backend.running:
            self.backend.update()
        self.backend.update()
        store = self.backend.get_store()
        assert store._repository.find(['py',
                           'test',
                           'tkinter',
                           'testing',
                           'data',
                           'filetest.py',
                           'TestClass'])
        
def test_remote():
    class ChannelMock:
        def __init__(self):
            self.sendlist = []
        def send(self, value):
            self.sendlist.append(value)
        def isclosed(self):
            return False
        
    channel = ChannelMock()
    backend.remote(channel, args = [str(datadir / 'filetest.py')], tests = [])
    #py.std.pprint.pprint(channel.sendlist)
    assert channel.sendlist
    
