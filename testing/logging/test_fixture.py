import logging

import pytest
from _pytest.logging import catch_log_records_key

logger = logging.getLogger(__name__)
sublogger = logging.getLogger(__name__ + ".baz")


def test_fixture_help(testdir):
    result = testdir.runpytest("--fixtures")
    result.stdout.fnmatch_lines(["*caplog*"])


def test_change_level(caplog):
    caplog.set_level(logging.INFO)
    logger.debug("handler DEBUG level")
    logger.info("handler INFO level")

    caplog.set_level(logging.CRITICAL, logger=sublogger.name)
    sublogger.warning("logger WARNING level")
    sublogger.critical("logger CRITICAL level")

    assert "DEBUG" not in caplog.text
    assert "INFO" in caplog.text
    assert "WARNING" not in caplog.text
    assert "CRITICAL" in caplog.text


def test_change_level_undo(testdir):
    """Ensure that 'set_level' is undone after the end of the test"""
    testdir.makepyfile(
        """
        import logging

        def test1(caplog):
            caplog.set_level(logging.INFO)
            # using + operator here so fnmatch_lines doesn't match the code in the traceback
            logging.info('log from ' + 'test1')
            assert 0

        def test2(caplog):
            # using + operator here so fnmatch_lines doesn't match the code in the traceback
            logging.info('log from ' + 'test2')
            assert 0
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*log from test1*", "*2 failed in *"])
    result.stdout.no_fnmatch_line("*log from test2*")


def test_with_statement(caplog):
    with caplog.at_level(logging.INFO):
        logger.debug("handler DEBUG level")
        logger.info("handler INFO level")

        with caplog.at_level(logging.CRITICAL, logger=sublogger.name):
            sublogger.warning("logger WARNING level")
            sublogger.critical("logger CRITICAL level")

    assert "DEBUG" not in caplog.text
    assert "INFO" in caplog.text
    assert "WARNING" not in caplog.text
    assert "CRITICAL" in caplog.text


def test_log_access(caplog):
    caplog.set_level(logging.INFO)
    logger.info("boo %s", "arg")
    assert caplog.records[0].levelname == "INFO"
    assert caplog.records[0].msg == "boo %s"
    assert "boo arg" in caplog.text


def test_messages(caplog):
    caplog.set_level(logging.INFO)
    logger.info("boo %s", "arg")
    logger.info("bar %s\nbaz %s", "arg1", "arg2")
    assert "boo arg" == caplog.messages[0]
    assert "bar arg1\nbaz arg2" == caplog.messages[1]
    assert caplog.text.count("\n") > len(caplog.messages)
    assert len(caplog.text.splitlines()) > len(caplog.messages)

    try:
        raise Exception("test")
    except Exception:
        logger.exception("oops")

    assert "oops" in caplog.text
    assert "oops" in caplog.messages[-1]
    # Tracebacks are stored in the record and not added until the formatter or handler.
    assert "Exception" in caplog.text
    assert "Exception" not in caplog.messages[-1]


def test_record_tuples(caplog):
    caplog.set_level(logging.INFO)
    logger.info("boo %s", "arg")

    assert caplog.record_tuples == [(__name__, logging.INFO, "boo arg")]


def test_unicode(caplog):
    caplog.set_level(logging.INFO)
    logger.info("bū")
    assert caplog.records[0].levelname == "INFO"
    assert caplog.records[0].msg == "bū"
    assert "bū" in caplog.text


def test_clear(caplog):
    caplog.set_level(logging.INFO)
    logger.info("bū")
    assert len(caplog.records)
    assert caplog.text
    caplog.clear()
    assert not len(caplog.records)
    assert not caplog.text


@pytest.fixture
def logging_during_setup_and_teardown(caplog):
    caplog.set_level("INFO")
    logger.info("a_setup_log")
    yield
    logger.info("a_teardown_log")
    assert [x.message for x in caplog.get_records("teardown")] == ["a_teardown_log"]


def test_caplog_captures_for_all_stages(caplog, logging_during_setup_and_teardown):
    assert not caplog.records
    assert not caplog.get_records("call")
    logger.info("a_call_log")
    assert [x.message for x in caplog.get_records("call")] == ["a_call_log"]

    assert [x.message for x in caplog.get_records("setup")] == ["a_setup_log"]

    # This reaches into private API, don't use this type of thing in real tests!
    assert set(caplog._item._store[catch_log_records_key]) == {"setup", "call"}


def test_ini_controls_global_log_level(testdir):
    testdir.makepyfile(
        """
        import pytest
        import logging
        def test_log_level_override(request, caplog):
            plugin = request.config.pluginmanager.getplugin('logging-plugin')
            assert plugin.log_level == logging.ERROR
            logger = logging.getLogger('catchlog')
            logger.warning("WARNING message won't be shown")
            logger.error("ERROR message will be shown")
            assert 'WARNING' not in caplog.text
            assert 'ERROR' in caplog.text
    """
    )
    testdir.makeini(
        """
        [pytest]
        log_level=ERROR
    """
    )

    result = testdir.runpytest()
    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_caplog_can_override_global_log_level(testdir):
    testdir.makepyfile(
        """
        import pytest
        import logging
        def test_log_level_override(request, caplog):
            logger = logging.getLogger('catchlog')
            plugin = request.config.pluginmanager.getplugin('logging-plugin')
            assert plugin.log_level == logging.WARNING

            logger.info("INFO message won't be shown")

            caplog.set_level(logging.INFO, logger.name)

            with caplog.at_level(logging.DEBUG, logger.name):
                logger.debug("DEBUG message will be shown")

            logger.debug("DEBUG message won't be shown")

            with caplog.at_level(logging.CRITICAL, logger.name):
                logger.warning("WARNING message won't be shown")

            logger.debug("DEBUG message won't be shown")
            logger.info("INFO message will be shown")

            assert "message won't be shown" not in caplog.text
    """
    )
    testdir.makeini(
        """
        [pytest]
        log_level=WARNING
    """
    )

    result = testdir.runpytest()
    assert result.ret == 0


def test_caplog_captures_despite_exception(testdir):
    testdir.makepyfile(
        """
        import pytest
        import logging
        def test_log_level_override(request, caplog):
            logger = logging.getLogger('catchlog')
            plugin = request.config.pluginmanager.getplugin('logging-plugin')
            assert plugin.log_level == logging.WARNING

            logger.info("INFO message won't be shown")

            caplog.set_level(logging.INFO, logger.name)

            with caplog.at_level(logging.DEBUG, logger.name):
                logger.debug("DEBUG message will be shown")
                raise Exception()
    """
    )
    testdir.makeini(
        """
        [pytest]
        log_level=WARNING
    """
    )

    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*DEBUG message will be shown*"])
    assert result.ret == 1

