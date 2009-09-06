import py

def test_functional(testdir):
    testdir.makepyfile("""
        def test_pass():
            pass
    """)
    testdir.runpytest("--hooklog=hook.log")
    s = testdir.tmpdir.join("hook.log").read()
    assert s.find("pytest_sessionstart") != -1
    assert s.find("ItemTestReport") != -1
    assert s.find("sessionfinish") != -1
