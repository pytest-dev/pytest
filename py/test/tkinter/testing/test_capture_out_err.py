import py
from py.__.test.tkinter import backend
ReportBackend = backend.ReportBackend

datadir = py.magic.autopath().dirpath('data')

def test_capture_out_err():
    config = py.test.config._reparse([datadir/'filetest.py'])
    backend = ReportBackend()
    backend.start_tests(config = config,
                                 args = config.args, 
                                 tests = [])
    while backend.running:
        backend.update()
    backend.update()
    store = backend.get_store()
    assert len(store.get(failed = True)) == 1
    failed = store.get(failed = True)[0]
    assert failed.stdout == 'STDOUT'
    assert failed.stderr == 'STDERR'
