def test_execnetplugin(testdir):
    reprec = testdir.inline_runsource("""
        import py
        import sys
        def test_hello():
            sys._gw = py.execnet.PopenGateway()
        def test_world():
            assert hasattr(sys, '_gw')
            assert sys._gw not in sys._gw._cleanup._activegateways
            
    """, "-s", "--debug")
    reprec.assertoutcome(passed=2)
