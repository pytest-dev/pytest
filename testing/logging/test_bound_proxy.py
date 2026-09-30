"""Unit-level regression tests for the bound proxy handler (#15064).

These drive ``catching_logs`` directly, which is where the proxy lifecycle
lives, and assert the exact behaviours the review asked for. End-to-end
behaviour (caplog, reports, live logs, --log-file) is covered in
test_fixture.py / test_reporting.py.
"""

from __future__ import annotations

from collections.abc import Iterator
import gc
import io
import logging
import threading
import weakref

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
            return True  # pragma: no cover - never called; that is the point

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
                pass  # pragma: no cover - __enter__ raises before this line
    finally:
        # Restore a real list: leaving the poisoned one installed would break
        # every later capturing_logs scope, including pytest's own session ones.
        bad.handlers = []

    # Nothing of pytest's is left behind on root or on the loggers.
    assert not any(h is handler for h in root.handlers)
    assert not [h for h in good.handlers if isinstance(h, _BoundProxyHandler)]
    assert _count(stream, "anything") == 0


def test_detached_proxy_ignores_direct_handle_call() -> None:
    """Calling ``handle()`` on a retained proxy after detach does nothing.

    The proxy is gone from ``logger.handlers`` once capture ends, so a later
    ``logger.warning()`` never reaches it. This covers someone who kept a
    reference to the proxy and calls it directly: it must not resurrect
    capture, nor raise.
    """
    logger = _make_logger("retained")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = _proxy_for(logger)
    proxy.handle(
        logging.LogRecord("retained", logging.WARNING, __file__, 1, "late", (), None)
    )
    assert _count(stream, "late") == 0


def test_finite_nested_record_is_captured_not_dropped() -> None:
    """A real handler logging one finite nested record must not lose it.

    The proxy forwards into the real handler, which may log one further record
    from its own ``emit()``. That nested record is a distinct record and the
    un-proxied handler would have captured it, so it must be captured here too:
    the real handler's lock is an ``RLock``, so the finite nesting terminates
    on its own and needs no reentrancy guard.

    A handler that logs *unconditionally* from its own ``emit()`` still
    recurses, but it does so identically without a proxy (the stdlib has the
    same reentrant lock), so that is not something the proxy changes.
    """
    emitted: list[str] = []

    class LoggingBack(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            emitted.append(record.getMessage())
            if record.getMessage() == "outer":
                # One finite nested record, then stop.
                logger.warning("inner")

    logger = _make_logger("recursive")
    real = LoggingBack()

    with catching_logs(real, level=logging.DEBUG):
        logger.warning("outer")

    assert emitted == ["outer", "inner"]


def test_setlevel_on_proxy_reaches_the_real_handler() -> None:
    """``setLevel`` on the proxy must reach the real handler.

    The proxy is a view of the real handler, so a level written through it is
    the level that is actually in force -- dropping the write would leave
    ``logger.handlers`` advertising a level that does not apply.
    """
    logger = _make_logger("j")
    stream, handler = _capture()
    with catching_logs(handler, level=logging.DEBUG):
        proxy = next(h for h in logger.handlers if isinstance(h, _BoundProxyHandler))
        proxy.setLevel(logging.CRITICAL)
        assert proxy.level == logging.CRITICAL
        logger.warning("m")
    # The record is now below the real handler's level, so it is not handled.
    assert _count(stream, "m") == 0


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
            self.acquire()  # pragma: no cover - only taken on Python 3.14+

        def __exit__(self, *exc: object) -> None:
            self.release()  # pragma: no cover - only taken on Python 3.14+

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
            pytest.fail(  # pragma: no cover - only on a reintroduced deadlock
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
            pass  # pragma: no cover - setLevel raises before any record

    _make_logger("o")
    handler = FailingLevel()
    root = logging.getLogger()
    with pytest.raises(RuntimeError):
        with catching_logs(handler, level=logging.DEBUG):
            pass  # pragma: no cover - __enter__ raises before this line
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


# --------------------------------------------------------------------------
# Regression coverage named in review #2 on #15075. Each of these fails on the
# previous head (or on the merge base) and pins the corrected behaviour.


def test_shared_handlers_list_transition_does_not_lose_sibling() -> None:
    """Two loggers sharing one ``handlers`` list, one flips ``propagate``.

    A list with more than one owner gets the real handler attached directly
    (the conservative fallback -- a single proxy cannot know which owner a
    shared-list visit is for), so the sibling's record is captured through
    the list itself and is never lost when the other owner starts
    propagating.
    """
    a = _make_logger("shared.a")
    b = _make_logger("shared.b")
    shared: list[logging.Handler] = []
    a.handlers = shared
    b.handlers = shared

    stream, handler = _capture()
    with catching_logs(handler):
        # Direct attachment for the shared list, not a proxy: the real
        # handler is in the list once, claimed by identity.
        assert not [h for h in shared if isinstance(h, _BoundProxyHandler)]
        assert sum(h is handler for h in shared) == 1
        a.propagate = True
        b.error("from-b")

    assert _count(stream, "from-b") == 1


def test_shared_handlers_list_transition_keeps_merge_base_behaviour() -> None:
    """Shared lists deliberately retain the pre-proxy transition limitation.

    With direct attachment on a shared list, a sibling that stays
    non-propagating always has its record captured (no lost records), while
    a record from the owner that flipped ``propagate`` mid-scope is handled
    once via the list and once via root -- exactly what the merge base did.
    Proxying shared lists cannot do better without per-owner routing the
    stdlib dispatch does not provide, so the conservative behaviour wins.
    """
    a = _make_logger("dup.a")
    b = _make_logger("dup.b")
    shared: list[logging.Handler] = []
    a.handlers = shared
    b.handlers = shared

    stream, handler = _capture()
    with catching_logs(handler):
        a.propagate = True
        b.error("only-once")
        a.error("via-root")

    assert _count(stream, "only-once") == 1
    # Merge-base behaviour for a mid-scope False->True flip on a shared
    # list: the list attachment and the root attachment both see it.
    assert _count(stream, "via-root") == 2


def test_finite_nested_record_from_real_handler_emit() -> None:
    """A handler logging one distinct record from its own ``emit()`` keeps it.

    The record is finite, so the reentrant lock terminates the nesting on its
    own; the proxy must not swallow it.
    """
    emitted: list[str] = []

    class Nested(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.once = False

        def emit(self, record: logging.LogRecord) -> None:
            emitted.append(record.getMessage())
            if not self.once and record.getMessage() == "outer":
                self.once = True
                logger.warning("inner")

    logger = _make_logger("nested.emit")
    with catching_logs(Nested()):
        logger.error("outer")

    assert emitted == ["outer", "inner"]


def test_pre_existing_target_filter_survives_teardown() -> None:
    """A filter already on the real handler is not removed at detach.

    Adding it again through the proxy must not make the proxy claim ownership
    of it: teardown would then delete a filter the caller installed.
    """
    logger = _make_logger("preexisting")
    _stream, handler = _capture()
    pre = logging.Filter("pre-existing")
    handler.addFilter(pre)

    with catching_logs(handler):
        proxy = _proxy_for(logger)
        proxy.addFilter(pre)  # same object, added again via the proxy
        assert any(f is pre for f in handler.filters)

    assert any(f is pre for f in handler.filters), (
        "teardown removed a filter the proxy did not add"
    )


def test_pre_existing_filter_still_applies_after_teardown() -> None:
    """The surviving filter must keep filtering, not merely survive."""
    logger = _make_logger("preexisting2")
    stream, handler = _capture()

    def only_warnings(record: logging.LogRecord) -> bool:
        return record.levelno >= logging.WARNING

    handler.addFilter(only_warnings)
    with catching_logs(handler):
        logger.info("dropped")
        logger.warning("kept")
    assert _count(stream, "dropped") == 0
    assert _count(stream, "kept") == 1
    # Still in force after the context ended.
    logger.info("dropped-too")
    assert _count(stream, "dropped-too") == 0


def test_proxy_delegates_level_filters_and_formatter() -> None:
    """The proxy is a view: level, filters and formatter are the real ones."""
    logger = _make_logger("view")
    _stream, handler = _capture()
    with catching_logs(handler):
        proxy = _proxy_for(logger)
        # level is a view in both directions
        assert proxy.level == logging.DEBUG
        handler.setLevel(logging.ERROR)
        assert proxy.level == logging.ERROR
        # filters list is the real handler's
        f = logging.Filter("f")
        proxy.addFilter(f)
        assert any(x is f for x in handler.filters)
        assert proxy.filters is handler.filters
        # formatter is the real handler's
        proxy.setFormatter(logging.Formatter("VIEW:%(message)s"))
        assert handler.formatter is not None
        assert handler.formatter._fmt == "VIEW:%(message)s"
        proxy.removeFilter(f)
        assert not any(x is f for x in handler.filters)


def test_detach_releases_strong_references_and_is_inert() -> None:
    """Final detach clears the proxy's strong refs and makes it inert."""
    logger = _make_logger("detach")
    proxies: list[_BoundProxyHandler] = []
    with catching_logs(logging.StreamHandler(io.StringIO())):
        proxies.append(_proxy_for(logger))
    proxy = proxies[0]

    assert proxy._is_detached
    assert proxy.logger is None
    assert proxy.real_handler is None
    assert proxy._group == ()
    # A late handle() is a safe no-op, not an AttributeError.
    record = logging.LogRecord("detach", logging.ERROR, "p", 1, "late", (), None)
    assert proxy.handle(record) is False


def test_capture_handler_is_not_held_by_detached_proxy() -> None:
    """A detached proxy must not pin the capture handler alive."""
    import gc
    import weakref

    logger = _make_logger("gcpin")
    handler = logging.StreamHandler(io.StringIO())
    with catching_logs(handler):
        # Assert the proxy exists so the handler is exercised; the point of the
        # test is what happens to ``handler`` once the proxy is detached.
        assert _proxy_for(logger) is not None
        logger.error("x")
    ref = weakref.ref(handler)
    del handler
    gc.collect()
    assert ref() is None, "detached proxy kept the capture handler alive"


def test_unhashable_logger_can_be_captured() -> None:
    """A ``Logger`` subclass with ``__hash__ = None`` must not break entry.

    Keying the proxy-target cache by the logger would raise ``TypeError`` here.
    """
    root = logging.getLogger()

    class UnhashableLogger(logging.Logger):
        __hash__ = None  # type: ignore[assignment]

    logger = UnhashableLogger("unhashable")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    root.manager.loggerDict["unhashable"] = logger

    stream, handler = _capture()
    with catching_logs(handler):
        logger.error("from-unhashable")

    assert _count(stream, "from-unhashable") == 1


def test_nested_contexts_share_one_direct_claim_for_shared_list() -> None:
    """Overlapping scopes over a shared list claim one direct attachment."""
    a = _make_logger("nested_ctx.a")
    b = _make_logger("nested_ctx.b")
    shared: list[logging.Handler] = []
    a.handlers = shared
    b.handlers = shared

    stream, handler = _capture()
    with catching_logs(handler):
        with catching_logs(handler):
            # Shared list -> direct attachment; the inner scope reuses the
            # outer scope's copy instead of adding a second one.
            assert not [h for h in shared if isinstance(h, _BoundProxyHandler)]
            assert sum(h is handler for h in shared) == 1, (
                "nested scopes must share one claim"
            )
            b.error("inner-record")
        # Outer scope still active: the claim is still attached.
        assert any(h is handler for h in shared)
        b.error("outer-record")

    # Distinct needles: "inner-record" is a substring of neither, and the two
    # records are counted separately.
    assert _count(stream, "inner-record") == 1
    assert _count(stream, "outer-record") == 1
    # Both contexts exited: nothing left behind.
    assert not [h for h in shared if h is handler]


def test_handlers_list_replaced_between_catches_is_not_stale() -> None:
    """Replacing a logger's ``handlers`` list between captures is detected.

    The target cache may not attach to the list that was cached during the
    first capture; the second capture must reach the logger's *current*
    list. The cache only stores the ``id()`` of each list, so the replaced
    list (and any unrelated user handler inside it) is never retained.
    """
    logger = _make_logger("cache.replace")
    old_list: list[logging.Handler] = logger.handlers
    user_handler = logging.NullHandler()
    old_list.append(user_handler)

    stream, handler = _capture()
    with catching_logs(handler):
        logger.error("first")
    assert _count(stream, "first") == 1

    fresh: list[logging.Handler] = []
    logger.handlers = fresh
    with catching_logs(handler):
        assert any(isinstance(h, _BoundProxyHandler) for h in fresh), (
            "capture must attach to the logger's current list"
        )
        logger.error("second")
    assert _count(stream, "second") == 1
    # The cache must not retain the replaced list. Plain lists are not
    # weak-referenceable, so use the user handler still sitting in it as a
    # liveness probe: if the cache held the old list, the handler (and the
    # list) could not be collected.
    handler_alive = weakref.ref(user_handler)
    del old_list, logger, user_handler
    gc.collect()
    assert handler_alive() is None
