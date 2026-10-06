"""Unit tests for the bound proxy handler used by ``catching_logs`` (#15064).

These drive ``catching_logs`` directly, which is where the proxy lifecycle
lives. End-to-end behaviour (caplog, reports, live logs, ``--log-file``) is
covered in ``test_fixture.py`` / ``test_reporting.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
import io
import logging

from _pytest.logging import _BoundProxyHandler
from _pytest.logging import catching_logs
import pytest


@pytest.fixture(autouse=True)
def _clean_logging() -> Iterator[None]:
    """Isolate each test from the ambient logging configuration."""
    root = logging.getLogger()
    saved_root_handlers = list(root.handlers)
    saved_level = root.level
    saved_dict = dict(root.manager.loggerDict)
    for name in list(root.manager.loggerDict):
        del root.manager.loggerDict[name]
    root.handlers.clear()
    root.setLevel(logging.WARNING)
    try:
        yield
    finally:
        for name in list(root.manager.loggerDict):
            del root.manager.loggerDict[name]
        root.manager.loggerDict.update(saved_dict)
        root.handlers.clear()
        root.handlers.extend(saved_root_handlers)
        root.setLevel(saved_level)


def _make_logger(name: str, *, propagate: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = propagate
    return logger


def _capture() -> tuple[io.StringIO, logging.Handler]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    return stream, handler


def test_proxy_captures_once_when_propagation_enabled() -> None:
    """The original bug: a non-propagating logger which starts propagating."""
    logger = _make_logger("a")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.propagate = True
        logger.warning("m")
    assert stream.getvalue().count("m") == 1


def test_proxy_captures_while_non_propagating() -> None:
    """A logger which stays non-propagating is still captured (#3697)."""
    logger = _make_logger("b")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.warning("m")
    assert stream.getvalue().count("m") == 1


def test_no_proxy_for_fully_propagating_logger() -> None:
    """Loggers that propagate throughout must not get a proxy at all."""
    _make_logger("c.plain", propagate=True)
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logging.getLogger("c.plain").warning("m")
    assert stream.getvalue().count("m") == 1
    assert not [
        h
        for h in logging.getLogger("c.plain").handlers
        if isinstance(h, _BoundProxyHandler)
    ]


def test_ancestor_of_non_propagating_logger_gets_a_proxy() -> None:
    """An ancestor which becomes the new barrier mid-test still captures once."""
    parent = _make_logger("p", propagate=True)
    child = _make_logger("p.child")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        child.propagate = True
        parent.propagate = False
        child.warning("m")
    assert stream.getvalue().count("m") == 1


def test_logger_becoming_non_propagating_between_scopes_is_captured() -> None:
    """Selection is not cached, so a logger made non-propagating after a first
    scope is still captured in the next one (#15064)."""
    logger = _make_logger("late", propagate=True)
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.warning("first")
    logger.propagate = False
    with catching_logs(handler, level=logging.DEBUG):
        logger.warning("second")
    assert stream.getvalue().count("first") == 1
    assert stream.getvalue().count("second") == 1


def test_proxy_forwards_level_filters_and_formatter() -> None:
    """The proxy is a live view of the real handler, not a copy."""
    logger = _make_logger("view")
    _, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
        proxy.setLevel(logging.ERROR)
        assert handler.level == logging.ERROR
        assert proxy.level == logging.ERROR
        proxy.addFilter(logging.Filter())
        assert proxy.filters == handler.filters
        fmt = logging.Formatter("%(message)s!")
        proxy.setFormatter(fmt)
        assert handler.formatter is fmt


def test_proxy_property_setters_reach_the_real_handler() -> None:
    """Direct attribute assignment through the proxy updates the real handler."""
    logger = _make_logger("setters")
    _, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
        proxy.level = logging.ERROR
        assert handler.level == logging.ERROR
        filters = [logging.Filter()]
        proxy.filters = filters  # type: ignore[assignment]
        assert handler.filters == filters
        proxy.formatter = logging.Formatter("%(message)s!")
        assert handler.formatter is not None


def test_proxy_forwards_when_emitted_directly() -> None:
    """A record driven straight through ``emit()`` is forwarded to the real
    handler while the bound logger is non-propagating."""
    logger = _make_logger("emit")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
        proxy.emit(logging.LogRecord("emit", logging.WARNING, "", 0, "m", (), None))
    assert stream.getvalue().count("m") == 1


def test_proxy_skips_forwarding_when_real_handler_attached_directly() -> None:
    """The real handler on the logger itself already handles the record, so the
    proxy must not forward a second copy."""
    logger = _make_logger("direct")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.addHandler(handler)
        logger.warning("m")
    assert stream.getvalue().count("m") == 1


def test_detached_proxy_is_inert() -> None:
    """A proxy used after its scope ended does not forward or raise."""
    logger = _make_logger("inert")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
    record = logging.LogRecord("inert", logging.WARNING, "", 0, "m", (), None)
    assert proxy.handle(record) is False
    proxy.emit(record)
    assert stream.getvalue() == ""
    # Property accessors on a detached proxy are also safe no-ops.
    assert proxy.level == logging.NOTSET
    assert proxy.filters == []
    assert proxy.formatter is None
    proxy.level = logging.ERROR
    proxy.filters = []
    proxy.formatter = None
    # ...as are the handler methods, which forward to the (now absent) real
    # handler.
    proxy.setLevel(logging.ERROR)
    proxy.addFilter(logging.Filter())
    proxy.removeFilter(logging.Filter())
    proxy.setFormatter(logging.Formatter("%(message)s"))


def test_proxy_add_filter_is_idempotent() -> None:
    """Adding the same filter object twice only installs it once."""
    logger = _make_logger("addfilter")
    _, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
        filt = logging.Filter()
        proxy.addFilter(filt)
        proxy.addFilter(filt)
        assert handler.filters.count(filt) == 1


def test_proxy_remove_filter_matches_and_ignores_absent() -> None:
    """``removeFilter`` removes a present filter by identity and is a no-op for
    one that was never added."""
    logger = _make_logger("removefilter")
    _, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
        present = logging.Filter()
        proxy.addFilter(present)
        proxy.removeFilter(logging.Filter())  # not present: no-op
        assert present in handler.filters
        proxy.removeFilter(present)
        assert present not in handler.filters


def test_remove_handler_by_identity_ignores_absent_handler() -> None:
    """The identity remover is a no-op when the handler is not on the logger."""
    from _pytest.logging import _remove_handler_by_identity

    logger = _make_logger("remover")
    other = logging.StreamHandler()
    existing = logging.StreamHandler()
    logger.addHandler(existing)
    _remove_handler_by_identity(logger, other)  # absent: nothing removed
    assert existing in logger.handlers


def test_proxy_removed_externally_is_still_closed_on_exit() -> None:
    """A proxy a user stripped from the logger mid-scope is still closed at
    teardown, and removal from the remembered list is a no-op."""
    logger = _make_logger("external")
    _, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
        logger.removeHandler(proxy)
    assert proxy.real_handler is None


def test_proxy_detached_on_exit_does_not_forward() -> None:
    """A proxy kept past the context is inert and releases the real handler."""
    logger = _make_logger("gone")
    _, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
    assert not any(h is proxy for h in logger.handlers)
    assert proxy.real_handler is None
    assert (
        proxy.handle(logging.LogRecord("gone", logging.WARNING, "", 0, "m", (), None))
        is False
    )


def test_detach_does_not_close_real_handler() -> None:
    _make_logger("keep")
    _, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        pass
    # The real handler is reused across phases; detaching the proxy must not
    # close it.
    assert not getattr(handler, "_closed")


def test_nested_scopes_share_one_proxy() -> None:
    """Overlapping scopes over the same handler must not double-forward."""
    logger = _make_logger("nested")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        with catching_logs(handler, level=logging.DEBUG):
            logger.warning("m")
        # Still one proxy while the outer scope is active.
        assert (
            len([h for h in logger.handlers if isinstance(h, _BoundProxyHandler)]) == 1
        )
    assert stream.getvalue().count("m") == 1
    assert not [h for h in logger.handlers if isinstance(h, _BoundProxyHandler)]
