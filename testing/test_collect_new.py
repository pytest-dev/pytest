def test_symlink_in_sandbox(testdir):
    appdir = testdir.mkdir("app")
    testdir.makepyfile(
        **{
            "app/__init__.py": """import pleasedontimportme""",
            "app/test.py": """
            def test_pass():
                pass
        """,
        }
    )
    sandbox = testdir.mkdir("sandbox")
    symlink = sandbox.join("test_symlink.py")
    symlink.mksymlinkto(appdir.join("test.py"))

    result = testdir.runpytest(str(symlink))
    result.stdout.fnmatch_lines(["*= 1 passed in *="])
