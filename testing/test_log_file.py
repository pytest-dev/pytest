import os

from _pytest.pytester import Pytester


def test_log_file_verbose(pytester: Pytester) -> None:
    log_file = str(pytester.path.joinpath("pytest.log"))

    pytester.makepyfile(
        """
        import logging
        def test_verbose1():
            logging.info("test 1")

        def test_verbose2():
            logging.warning("test 2")
    """
    )

    result = pytester.runpytest(
        "-s", f"--log-file={log_file}", "--log-file-verbose=1", "--log-file-level=INFO"
    )

    rec = pytester.inline_run()
    rec.assertoutcome(passed=2)

    # make sure that we get a '0' exit code for the testsuite
    assert result.ret == 0
    assert os.path.isfile(log_file)
    with open(log_file, encoding="utf-8") as rfh:
        contents = rfh.read()

        for s in [
            "Running at test_log_file_verbose.py::test_verbose1",
            "test 1",
            "Running at test_log_file_verbose.py::test_verbose2",
            "test 2",
        ]:
            assert s in contents


def test_log_file_verbose0(pytester: Pytester) -> None:
    log_file = str(pytester.path.joinpath("pytest.log"))

    pytester.makepyfile(
        """
        import logging
        def test_verbose1():
            logging.info("test 1")

        def test_verbose2():
            logging.warning("test 2")
    """
    )

    result = pytester.runpytest(
        "-s", f"--log-file={log_file}", "--log-file-verbose=0", "--log-file-level=INFO"
    )

    rec = pytester.inline_run()
    rec.assertoutcome(passed=2)

    # make sure that we get a '0' exit code for the testsuite
    assert result.ret == 0
    assert os.path.isfile(log_file)
    with open(log_file, encoding="utf-8") as rfh:
        contents = rfh.read()

        for s in ["test 1", "test 2"]:
            assert s in contents

        for s in [
            "Running at test_log_file_verbose0.py::test_verbose1",
            "Running at test_log_file_verbose.py::test_verbose2",
        ]:
            assert s not in contents
