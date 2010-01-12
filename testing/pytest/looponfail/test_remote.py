import py
py.test.importorskip("execnet")
from py.impl.test.looponfail.remote import LooponfailingSession, LoopState, RemoteControl 

class TestRemoteControl:
    def test_nofailures(self, testdir):
        item = testdir.getitem("def test_func(): pass\n")
        control = RemoteControl(item.config)
        control.setup()
        failures = control.runsession()
        assert not failures

    def test_failures_somewhere(self, testdir):
        item = testdir.getitem("def test_func(): assert 0\n")
        control = RemoteControl(item.config)
        control.setup()
        failures = control.runsession()
        assert failures 
        control.setup()
        item.fspath.write("def test_func(): assert 1\n")
        pyc = item.fspath.new(ext=".pyc")
        if pyc.check():
            pyc.remove()
        failures = control.runsession(failures)
        assert not failures

    def test_failure_change(self, testdir):
        modcol = testdir.getitem("""
            def test_func(): 
                assert 0
        """)
        control = RemoteControl(modcol.config)
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
        pyc = modcol.fspath.new(ext=".pyc")
        if pyc.check():
            pyc.remove()
        failures = control.runsession(failures)
        assert not failures
        control.setup()
        failures = control.runsession()
        assert failures
        assert str(failures).find("test_new") != -1

class TestLooponFailing:
    def test_looponfail_from_fail_to_ok(self, testdir):
        modcol = testdir.getmodulecol("""
            def test_one():
                x = 0
                assert x == 1
            def test_two():
                assert 1
        """)
        session = LooponfailingSession(modcol.config)
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

    def test_looponfail_from_one_to_two_tests(self, testdir):
        modcol = testdir.getmodulecol("""
            def test_one():
                assert 0
        """)
        session = LooponfailingSession(modcol.config)
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

    def test_looponfail_removed_test(self, testdir):
        modcol = testdir.getmodulecol("""
            def test_one():
                assert 0
            def test_two():
                assert 0
        """)
        session = LooponfailingSession(modcol.config)
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


    def test_looponfail_functional_fail_to_ok(self, testdir):
        p = testdir.makepyfile("""
            def test_one():
                x = 0
                assert x == 1
        """)
        child = testdir.spawn_pytest("-f %s" % p)
        child.expect("def test_one")
        child.expect("x == 1")
        child.expect("1 failed")
        child.expect("### LOOPONFAILING ####")
        child.expect("waiting for changes")
        p.write(py.code.Source("""
            def test_one():
                x = 1
                assert x == 1
        """))
        child.expect(".*1 passed.*")
        child.kill(15)

