import py
from py.__.test.testing import suptest
from py.__.test.looponfail.remote import LooponfailingSession, LoopState, RemoteControl 
from py.__.test import event

def getevent(l, evtype):
    result = getevents(l, evtype)
    if not result:
        raise ValueError("event %r not found in %r" %(evtype, l))
    return result[0]

def getevents(l, evtype):
    result = []
    for ev in l:
        if isinstance(ev, evtype):
            result.append(ev)
    return result
    
        
class TestRemoteControl(suptest.InlineCollection):
    def test_nofailures(self):
        item = self.getitem("def test_func(): pass\n")
        events = []
        control = RemoteControl(item._config)
        control.setup()
        failures = control.runsession()
        assert not failures

    def test_failures(self):
        item = self.getitem("def test_func(): assert 0\n")
        control = RemoteControl(item._config)
        control.setup()
        failures = control.runsession()
        assert failures 
        control.setup()
        item.fspath.write("def test_func(): assert 1\n")
        (item.fspath + "c").remove()
        failures = control.runsession(failures)
        assert not failures

    def test_failure_change(self):
        modcol = self.getitem("""
            def test_func(): 
                assert 0
        """)
        control = RemoteControl(modcol._config)
        control.setup()
        failures = control.runsession()
        assert failures 
        control.setup()
        modcol.fspath.write(py.code.Source("""
            def test_func():
                assert 1
            def test_new():
                assert 0
        """))
        (modcol.fspath + "c").remove()
        failures = control.runsession(failures)
        assert not failures
        control.setup()
        failures = control.runsession()
        assert failures
        assert str(failures).find("test_new") != -1

class TestLooponFailing(suptest.InlineCollection):
    def test_looponfailing_from_fail_to_ok(self):
        modcol = self.getmodulecol("""
            def test_one():
                x = 0
                assert x == 1
            def test_two():
                assert 1
        """)
        session = LooponfailingSession(modcol._config)
        loopstate = LoopState()
        session.remotecontrol.setup()
        session.loop_once(loopstate)
        assert len(loopstate.colitems) == 1
 
        modcol.fspath.write(py.code.Source("""
            def test_one():
                x = 15
                assert x == 15
            def test_two():
                assert 1
        """))
        assert session.statrecorder.check()
        session.loop_once(loopstate)
        assert not loopstate.colitems 

    def test_looponfailing_from_one_to_two_tests(self):
        modcol = self.getmodulecol("""
            def test_one():
                assert 0
        """)
        session = LooponfailingSession(modcol._config)
        loopstate = LoopState()
        session.remotecontrol.setup()
        loopstate.colitems = []
        session.loop_once(loopstate)
        assert len(loopstate.colitems) == 1

        modcol.fspath.write(py.code.Source("""
            def test_one():
                assert 1 # passes now
            def test_two():
                assert 0 # new and fails
        """))
        assert session.statrecorder.check()
        session.loop_once(loopstate)
        assert len(loopstate.colitems) == 0

        session.loop_once(loopstate)
        assert len(loopstate.colitems) == 1

    def test_looponfailing_removed_test(self):
        modcol = self.getmodulecol("""
            def test_one():
                assert 0
            def test_two():
                assert 0
        """)
        session = LooponfailingSession(modcol._config)
        loopstate = LoopState()
        session.remotecontrol.setup()
        loopstate.colitems = []
        session.loop_once(loopstate)
        assert len(loopstate.colitems) == 2

        modcol.fspath.write(py.code.Source("""
            def test_xxx(): # renamed test
                assert 0 
            def test_two():
                assert 1 # pass now
        """))
        assert session.statrecorder.check()
        session.loop_once(loopstate)
        assert len(loopstate.colitems) == 0

        session.loop_once(loopstate)
        assert len(loopstate.colitems) == 1
