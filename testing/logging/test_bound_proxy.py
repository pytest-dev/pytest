"""Unit-level regression tests for the bound proxy handler (#15064).

These drive ``catching_logs`` directly, which is where the proxy lifecycle
lives, and assert the exact behaviours the review asked for. End-to-end
behaviour (caplog, reports, live logs, --log-file) is covered in
test_fixture.py / test_reporting.py.
"""

from __future__ import annotations

from collections.abc import Iterator
import io
import logging
import threading

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


def _capture(handler_level: int = logging.DEBUG) -> tuple[io.StringIO, logging.Handler]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(handler_level)
    return stream, handler


def _count(stream: io.StringIO, needle: str) -> int:
    return stream.getvalue().count(needle)


def _proxy_for(logger: logging.Logger) -> _BoundProxyHandler:
    """The bound proxy pytest attached to ``logger`` in the current scope."""
    proxies = [h for h in logger.handlers if isinstance(h, _BoundProxyHandler)]
    assert proxies, f"no proxy attached to {logger.name}"
    return proxies[0]


def test_proxy_captures_once_when_propagation_enabled() -> None:
    """The original bug: a non-propagating logger which starts propagating."""
    logger = _make_logger("a")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.propagate = True
        logger.warning("m")
    assert _count(stream, "m") == 1


def test_proxy_captures_while_non_propagating() -> None:
    """A logger which stays non-propagating is still captured (#3697)."""
    logger = _make_logger("b")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.warning("m")
    assert _count(stream, "m") == 1


def test_no_proxy_for_fully_propagating_logger() -> None:
    """Loggers that propagate throughout must not get a proxy at all."""
    _make_logger("c.plain", propagate=True)
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logging.getLogger("c.plain").warning("m")
    assert _count(stream, "m") == 1
    assert not [
        h
        for h in logging.getLogger("c.plain").handlers
        if isinstance(h, _BoundProxyHandler)
    ]


def test_directly_attached_real_handler_is_not_duplicated() -> None:
    """If the real handler is on the logger too, it must not be handled twice."""
    logger = _make_logger("d")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.addHandler(handler)
        logger.warning("m")
    assert _count(stream, "m") == 1


def test_shared_handlers_list_is_not_duplicated() -> None:
    """Two non-propagating loggers sharing one handlers list."""
    shared: list[logging.Handler] = []
    a = _make_logger("e.a")
    b = _make_logger("e.b")
    a.handlers = shared
    b.handlers = shared
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        a.addHandler(handler)
        a.warning("m")
    assert _count(stream, "m") == 1


def test_aliased_root_handlers_is_not_duplicated() -> None:
    """A logger whose handlers list *is* root.handlers."""
    logger = _make_logger("f")
    logger.handlers = logging.getLogger().handlers
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.warning("m")
    assert _count(stream, "m") == 1


def test_identity_hostile_user_handler_survives_capture() -> None:
    """A user handler that compares equal to everything must not be removed."""

    class Hostile(logging.Handler):
        def __eq__(self, other: object) -> bool:
            return True

        __hash__ = object.__hash__

        def emit(self, record: logging.LogRecord) -> None:
            pass

    logger = _make_logger("g")
    hostile = Hostile()
    logger.addHandler(hostile)
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        logger.warning("m")
    assert _count(stream, "m") == 1
    assert any(h is hostile for h in logger.handlers), "user handler was removed"
    assert not any(h is handler for h in logger.handlers)


def test_detached_proxy_does_not_forward() -> None:
    """A proxy retained after the context must stop forwarding, and must not
    keep the capture handler alive."""
    logger = _make_logger("h")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxies = [h for h in logger.handlers if isinstance(h, _BoundProxyHandler)]
        assert proxies
        proxy = proxies[0]
    # Detached on exit: the proxy stops forwarding, and a retained reference
    # cannot resurrect capture or keep the capture handler alive.
    assert proxy._is_detached
    logger.warning("late")
    assert _count(stream, "late") == 0


def test_detach_does_not_close_real_handler() -> None:
    """The real handler is reused across phases, so it must survive detach."""
    _make_logger("i")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        pass
    assert not getattr(handler, "_closed", False)
    handler.handle(
        logging.LogRecord("i", logging.WARNING, __file__, 1, "after", (), None)
    )
    assert _count(stream, "after") == 1


def test_remove_filter_through_proxy_deactivates_it() -> None:
    """Removing a filter through the proxy must stop it applying, both while
    capture is live and on the real handler afterwards."""
    logger = _make_logger("rmfilter")
    stream, handler = _capture()

    class Reject(logging.Filter):
        def __init__(self) -> None:
            super().__init__()
            self.seen: list[str] = []

        def filter(self, record: logging.LogRecord) -> bool:
            self.seen.append(record.getMessage())
            return False

    reject = Reject()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = _proxy_for(logger)
        proxy.addFilter(reject)
        logger.warning("blocked")
        assert _count(stream, "blocked") == 0
        assert reject.seen == ["blocked"]

        proxy.removeFilter(reject)
        logger.warning("allowed")
        assert _count(stream, "allowed") == 1

    # And it is gone from the real handler too, so a later scope is unaffected.
    assert not any(f is reject for f in handler.filters)
    handler.handle(
        logging.LogRecord("rmfilter", logging.WARNING, __file__, 1, "later", (), None)
    )
    assert _count(stream, "later") == 1


def test_set_formatter_through_proxy_applies_to_captured_output() -> None:
    """A formatter set through the proxy must shape the captured text."""
    logger = _make_logger("fmt")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        _proxy_for(logger).setFormatter(
            logging.Formatter("FMT:%(levelname)s:%(message)s")
        )
        logger.warning("shaped")
    assert "FMT:WARNING:shaped" in stream.getvalue()


def test_set_formatter_through_proxy_accepts_none() -> None:
    """Passing None clears the formatter rather than raising."""
    logger = _make_logger("fmt.none")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = _proxy_for(logger)
        proxy.setFormatter(logging.Formatter("X:%(message)s"))
        proxy.setFormatter(None)
        logger.warning("plain")
    assert "X:plain" not in stream.getvalue()
    assert "plain" in stream.getvalue()


def test_emit_directly_on_proxy_forwards_while_non_propagating() -> None:
    """Calling ``emit()`` directly (as opposed to ``handle()``) must still
    forward for a non-propagating logger and be a no-op once it propagates."""
    logger = _make_logger("direct.emit")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = _proxy_for(logger)
        proxy.emit(
            logging.LogRecord(
                "direct.emit", logging.WARNING, __file__, 1, "viaemit", (), None
            )
        )
        assert _count(stream, "viaemit") == 1

        logger.propagate = True
        proxy.emit(
            logging.LogRecord(
                "direct.emit", logging.WARNING, __file__, 1, "skipped", (), None
            )
        )
        # A direct emit() does not walk the hierarchy, so the proxy must simply
        # not forward: the record was already sent to root's handler by the
        # logger's own callHandlers pass, and forwarding again would duplicate
        # it.
        assert _count(stream, "skipped") == 0


def test_emit_on_detached_proxy_is_a_no_op() -> None:
    """A detached proxy must not forward even when emit() is called directly."""
    logger = _make_logger("detached.emit")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = _proxy_for(logger)
    assert proxy._is_detached
    proxy.emit(
        logging.LogRecord(
            "detached.emit", logging.WARNING, __file__, 1, "nope", (), None
        )
    )
    assert _count(stream, "nope") == 0


def test_entry_failure_during_proxy_attachment_rolls_back() -> None:
    """A failure *while attaching proxies* must undo the partial setup.

    This is the path the transactional ``__enter__`` exists for: root already
    has pytest's handler by the time proxies are attached, so an error there
    would otherwise leave it attached with no scope left to remove it.
    """
    good = _make_logger("rollback.good")
    stream, handler = _capture()
    root = logging.getLogger()

    class Exploding(list):  # type: ignore[type-arg]
        """A handlers list that refuses new entries."""

        def append(self, item: object) -> None:
            raise RuntimeError("boom")

    bad = _make_logger("rollback.bad")
    bad.handlers = Exploding()
    try:
        with pytest.raises(RuntimeError):
            with catching_logs(handler, level=logging.DEBUG):
                pass
    finally:
        # Restore a real list: leaving the poisoned one installed would break
        # every later capturing_logs scope, including pytest's own session ones.
        bad.handlers = []

    # Nothing of pytest's is left behind on root or on the loggers.
    assert not any(h is handler for h in root.handlers)
    assert not [h for h in good.handlers if isinstance(h, _BoundProxyHandler)]
    assert _count(stream, "anything") == 0


def test_setlevel_on_proxy_is_ignored() -> None:
    """``setLevel`` on the proxy must not silently diverge from the real
    handler; the real handler's level governs."""
    logger = _make_logger("j")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
        proxy.setLevel(logging.CRITICAL)
        assert proxy.level == logging.DEBUG
        logger.warning("m")
    assert _count(stream, "m") == 1


def test_proxy_does_not_deadlock_with_real_handler_across_threads() -> None:
    """The proxy must not hold its own lock while invoking the real handler.

    ``logging.Handler.handle`` holds ``self.lock`` across ``emit``. If the proxy
    forwards to the real handler from there, it takes the real handler's lock
    while already holding its own, giving a ``proxy -> real`` order that another
    thread inverts as ``real -> proxy`` -- an ABBA deadlock.

    The check is the lock ORDER (deterministic), not the absence of a hang: a
    thread that already holds the real handler's lock must never find the proxy
    lock held by a thread waiting for the real one.
    """
    logger = _make_logger("k")
    handler = logging.StreamHandler(io.StringIO())
    handler.setLevel(logging.DEBUG)
    trace: list[str] = []
    trace_lock = threading.Lock()

    def note(message: str) -> None:
        with trace_lock:
            trace.append(message)

    class TracingRLock:
        """An RLock that records acquisition order across threads.

        Implements the context-manager protocol as well, because
        ``logging.Handler.handle()`` uses ``with self.lock:`` on newer
        Pythons (3.14+).
        """

        def __init__(self, name: str) -> None:
            self._rlock = threading.RLock()
            self._name = name

        def __enter__(self) -> None:
            self.acquire()

        def __exit__(self, *exc: object) -> None:
            self.release()

        def acquire(self, *args: object, **kwargs: object) -> bool:
            note(f"{threading.current_thread().name}:want:{self._name}")
            acquired = self._rlock.acquire()
            note(f"{threading.current_thread().name}:got:{self._name}")
            return acquired

        def release(self) -> None:
            self._rlock.release()
            note(f"{threading.current_thread().name}:rel:{self._name}")

    handler.lock = TracingRLock("REAL")  # type: ignore[assignment]
    proxy = _BoundProxyHandler(logger, handler)
    proxy.lock = TracingRLock("PROXY")  # type: ignore[assignment]
    logger.addHandler(proxy)

    ready = threading.Event()

    def other_thread() -> None:
        # Simulate a thread already inside the real handler (it holds its lock).
        handler.acquire()
        try:
            ready.set()
            logger.warning("from-B")
        finally:
            handler.release()

    def first_thread() -> None:
        ready.wait(5)
        logger.warning("from-A")

    other = threading.Thread(target=other_thread, daemon=True)
    first = threading.Thread(target=first_thread, daemon=True)
    other.start()
    first.start()
    first.join(timeout=10)
    other.join(timeout=10)

    assert not first.is_alive(), "deadlock: first thread did not finish"
    assert not other.is_alive(), "deadlock: other thread did not finish"

    # The inversion: a thread holding PROXY while waiting for REAL.
    for index, entry in enumerate(trace[:-1]):
        if entry.endswith(":got:PROXY") and trace[index + 1].endswith(":want:REAL"):
            pytest.fail(
                "proxy held its own lock while invoking the real handler: "
                f"{entry} -> {trace[index + 1]}"
            )


def test_entry_rolls_back_when_logger_is_unhashable() -> None:
    """A custom Logger with ``__hash__ = None`` must not break entry, and a
    failure must not leave pytest's handler attached to root.

    The logger's class is swapped in place because ``catching_logs`` walks
    ``manager.loggerDict``; the original class is restored in the ``finally``
    so the poisoned logger cannot leak into other tests.
    """

    class UnhashableLogger(logging.Logger):
        __hash__ = None  # type: ignore[assignment]

    _make_logger("l")
    broken = logging.getLogger("l.broken")
    broken.handlers.clear()
    broken.propagate = False
    original_class = broken.__class__
    broken.__class__ = UnhashableLogger
    stream, handler = _capture()
    try:
        with catching_logs(handler, level=logging.DEBUG):
            broken.warning("m")
    finally:
        broken.__class__ = original_class
        broken.handlers.clear()
    assert _count(stream, "m") == 1
    assert not any(h is handler for h in logging.getLogger().handlers)


def test_entry_failure_rolls_back_root_attachment() -> None:
    """A failure while attaching proxies must not leave pytest's handler on
    root with no scope left to remove it.

    The failure is injected by passing a handler whose ``setLevel`` raises --
    that happens inside ``__enter__`` before any proxy work -- and the logger
    population is restored by the autouse ``_clean_logging`` fixture, so no
    state leaks into the surrounding session.
    """

    class FailingLevel(logging.Handler):
        def setLevel(self, level: int | str) -> None:
            raise RuntimeError("boom")

        def emit(self, record: logging.LogRecord) -> None:
            pass

    _make_logger("o")
    handler = FailingLevel()
    root = logging.getLogger()
    with pytest.raises(RuntimeError):
        with catching_logs(handler, level=logging.DEBUG):
            pass
    assert not any(h is handler for h in root.handlers)


def test_nested_contexts_with_same_target_capture_once() -> None:
    """Overlapping contexts sharing one handler must not duplicate records."""
    logger = _make_logger("m")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        with catching_logs(handler, level=logging.DEBUG):
            logger.warning("m")
    assert _count(stream, "m") == 1


def test_exception_inside_context_still_detaches() -> None:
    """__exit__ must clean up when the body raises."""
    logger = _make_logger("n")
    _stream, handler = _capture()
    with pytest.raises(RuntimeError):
        with catching_logs(handler, level=logging.DEBUG):
            raise RuntimeError("boom")
    assert not any(h is handler for h in logging.getLogger().handlers)
    assert not [h for h in logger.handlers if isinstance(h, _BoundProxyHandler)]


def test_logger_created_after_first_capture_still_gets_a_proxy() -> None:
    """The proxy-target cache must not hide a logger that appears later.

    pytest re-enters ``catching_logs`` for every test phase, so the target set
    is cached; a logger created between two phases must still be picked up.
    """
    _make_logger("cache.first")
    _stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        pass

    late = _make_logger("cache.late")
    with catching_logs(handler, level=logging.DEBUG):
        proxies = [h for h in late.handlers if isinstance(h, _BoundProxyHandler)]
        assert len(proxies) == 1
        late.warning("m")
    assert _count(_stream, "m") == 1


def test_removed_logger_is_not_held_by_the_target_cache() -> None:
    """A logger deleted from ``loggerDict`` must not stay cached forever."""
    _make_logger("cache.gone")
    _stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        pass

    gone = logging.getLogger("cache.gone")
    del logging.getLogger().manager.loggerDict["cache.gone"]
    gone.handlers.clear()

    with catching_logs(handler, level=logging.DEBUG):
        assert not [h for h in gone.handlers if isinstance(h, _BoundProxyHandler)]
