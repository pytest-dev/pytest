# -*- coding: utf-8 -*-
import logging

import pytest

logger = logging.getLogger(__name__)
sublogger = logging.getLogger(__name__ + '.baz')


def test_fixture_help(testdir):
    result = testdir.runpytest('--fixtures')
    result.stdout.fnmatch_lines(['*caplog*'])


def test_change_level(caplog):
    caplog.set_level(logging.INFO)
    logger.debug('handler DEBUG level')
    logger.info('handler INFO level')

    caplog.set_level(logging.CRITICAL, logger=sublogger.name)
    sublogger.warning('logger WARNING level')
    sublogger.critical('logger CRITICAL level')

    assert 'DEBUG' not in caplog.text
    assert 'INFO' in caplog.text
    assert 'WARNING' not in caplog.text
    assert 'CRITICAL' in caplog.text


def test_with_statement(caplog):
    with caplog.at_level(logging.INFO):
        logger.debug('handler DEBUG level')
        logger.info('handler INFO level')

        with caplog.at_level(logging.CRITICAL, logger=sublogger.name):
            sublogger.warning('logger WARNING level')
            sublogger.critical('logger CRITICAL level')

    assert 'DEBUG' not in caplog.text
    assert 'INFO' in caplog.text
    assert 'WARNING' not in caplog.text
    assert 'CRITICAL' in caplog.text


def test_log_access(caplog):
    logger.info('boo %s', 'arg')
    assert caplog.records[0].levelname == 'INFO'
    assert caplog.records[0].msg == 'boo %s'
    assert 'boo arg' in caplog.text


def test_record_tuples(caplog):
    logger.info('boo %s', 'arg')

    assert caplog.record_tuples == [
        (__name__, logging.INFO, 'boo arg'),
    ]


def test_unicode(caplog):
    logger.info(u'bū')
    assert caplog.records[0].levelname == 'INFO'
    assert caplog.records[0].msg == u'bū'
    assert u'bū' in caplog.text


def test_clear(caplog):
    logger.info(u'bū')
    assert len(caplog.records)
    caplog.clear()
    assert not len(caplog.records)


@pytest.fixture
def logging_during_setup_and_teardown(caplog):
    logger.info('a_setup_log')
    yield
    logger.info('a_teardown_log')
    assert [x.message for x in caplog.get_handler('teardown').records] == ['a_teardown_log']


def test_caplog_captures_for_all_stages(caplog, logging_during_setup_and_teardown):
    assert not caplog.records
    assert not caplog.get_handler('call').records
    logger.info('a_call_log')
    assert [x.message for x in caplog.get_handler('call').records] == ['a_call_log']

    assert [x.message for x in caplog.get_handler('setup').records] == ['a_setup_log']

    # This reachers into private API, don't use this type of thing in real tests!
    assert set(caplog._item.catch_log_handlers.keys()) == {'setup', 'call'}
